import pandas as pd
import numpy as np
import torch
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    BioGptForSequenceClassification,
    Trainer,
    TrainingArguments,
    logging as hf_logging,
)

# --- Configuration ---
FILE_NAME = "radiology_reports.csv"
DELIMITER = ";"

# --- Feature Configuration ---
TEXT_COLUMNS = ["Observations", "Conclusion", "Recommendations", "Reason"]

# New: Tabular columns to serialize into text
TABULAR_COLUMNS = [
    # "Medical_Unit",
    "Hormonal_Therapy",
    "Family_History",
    "Age",
    "Children"
]
# We are intentionally omitting:
# - ID_R, Year, Month, LMP (per your instruction)
# - Full_Report (as we are combining the specific report sections)

TARGET_COLUMN = "BI-RADS" # The column we want to predict
MODEL_NAME = "microsoft/biogpt-large"
TEST_SIZE = 0.2  # 20% of data for testing
RANDOM_STATE = 42 # For reproducible results
OUTPUT_DIR = "./biogpt_birads_classifier"

# Set verbosity to 'info' to see progress bars (like tqdm)
hf_logging.set_verbosity_info()

def load_and_preprocess_data():
    """
    Loads the CSV, combines text and tabular fields, and maps labels.
    """
    print(f"--- Step 1: Loading Data from {FILE_NAME} ---")
    try:
        df = pd.read_csv(FILE_NAME, delimiter=DELIMITER)
    except FileNotFoundError:
        print(f"Error: File '{FILE_NAME}' not found.")
        print("Please make sure the file is in the same directory as the script.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        print("Please check the file format and delimiter.")
        sys.exit(1)

    print(f"Loaded {len(df)} reports.")

    # --- Text & Feature Preprocessing ---
    print("Preprocessing text and serializing tabular features...")
    
    # Fill any missing text fields with an empty string
    for col in TEXT_COLUMNS:
        df[col] = df[col].fillna("")
        
    # Fill missing tabular data with "Unknown"
    # We convert all to string to handle mixed types gracefully
    for col in TABULAR_COLUMNS:
        df[col] = df[col].fillna("Unknown").astype(str)

    # --- Create the combined 'text' field ---
    
    # 1. Create the main report text
    df['report_text'] = df[TEXT_COLUMNS].apply(
        lambda x: ' '.join(x.astype(str)), axis=1
    )
    
    # 2. Create the serialized metadata string
    # This creates a string like:
    # "Medical Unit: X. Hormonal Therapy: Y. Family History: Z. Age: A. Children: B."
    def create_metadata_string(row):
        parts = []
        parts.append(f"Medical Unit: {row['Medical_Unit']}")
        parts.append(f"Hormonal Therapy: {row['Hormonal_Therapy']}")
        parts.append(f"Family History: {row['Family_History']}")
        parts.append(f"Age: {row['Age']}")
        parts.append(f"Children: {row['Children']}")
        return ". ".join(parts) + "."

    df['metadata_text'] = df.apply(create_metadata_string, axis=1)

    # 3. Combine metadata and report text with a separator
    # The [REPORT] token helps the model distinguish metadata from the report
    df['text'] = df['metadata_text'] + " [REPORT] " + df['report_text']
    
    print("Example of combined text input:")
    print(df['text'].iloc[0])

    # --- Label Preprocessing ---
    # Drop rows where the target label is missing
    df = df.dropna(subset=[TARGET_COLUMN])
    
    # Get all unique BI-RADS values (e.g., 0, 1, 2, 4, 5, 6)
    # This automatically handles if a category like '3' is missing
    unique_labels = sorted(df[TARGET_COLUMN].unique())
    
    # FIX: Convert numpy.int64 to standard python int for JSON serialization
    unique_labels = [int(label) for label in unique_labels]
    
    # Create the label mappings required by the model
    # Model needs labels to be 0, 1, 2, 3...
    label2id = {label: i for i, label in enumerate(unique_labels)}
    id2label = {i: label for label, i in label2id.items()}
    num_labels = len(unique_labels)
    
    print(f"Found {num_labels} unique BI-RADS labels: {unique_labels}")
    print(f"Mapped labels to integers: {label2id}")
    
    # Create the final 'label' column with integer IDs
    df['label'] = df[TARGET_COLUMN].map(label2id)
    
    # Keep only the columns we need
    # We also keep TARGET_COLUMN for the final evaluation comparison
    final_df = df[['text', 'label', TARGET_COLUMN]]
    
    return final_df, label2id, id2label, num_labels

def tokenize_data(train_df, test_df):
    """
    Loads tokenizer and tokenizes the datasets.
    """
    print(f"--- Step 2: Loading Tokenizer ({MODEL_NAME}) ---")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    # Handle BioGPT's lack of a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    def tokenize_function(examples):
        # Truncate to the model's max input size
        # The new metadata text will take up some of the 512 tokens
        return tokenizer(
            examples['text'], 
            padding="max_length", 
            truncation=True, 
            max_length=512
        )

    print("Tokenizing datasets...")
    # Convert pandas DataFrames to Hugging Face Dataset objects
    train_dataset = Dataset.from_pandas(train_df)
    test_dataset = Dataset.from_pandas(test_df)
    
    # Apply tokenization
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    
    # Remove original columns to prepare for the model
    # Check for '__index_level_0__' which is sometimes added by from_pandas
    train_remove_cols = [TARGET_COLUMN, 'text']
    if '__index_level_0__' in tokenized_train.column_names:
        train_remove_cols.append('__index_level_0__')
        
    test_remove_cols = [TARGET_COLUMN, 'text']
    if '__index_level_0__' in tokenized_test.column_names:
        test_remove_cols.append('__index_level_0__')

    tokenized_train = tokenized_train.remove_columns(train_remove_cols)
    tokenized_test = tokenized_test.remove_columns(test_remove_cols)
    
    # Set format for PyTorch
    tokenized_train.set_format("torch")
    tokenized_test.set_format("torch")

    return tokenized_train, tokenized_test, tokenizer

def compute_metrics(p):
    """
    Calculates accuracy and F1-score for evaluation.
    """
    preds = np.argmax(p.predictions, axis=1)
    labels = p.label_ids
    
    accuracy = accuracy_score(labels, preds)
    # Use 'macro' average for F1-score to treat all classes equally
    f1 = f1_score(labels, preds, average="macro")
    
    return {
        "accuracy": accuracy,
        "f1_macro": f1,
    }

def train_model(
    tokenized_train, 
    tokenized_test, 
    tokenizer, 
    num_labels, 
    id2label, 
    label2id
):
    """
    Loads the model and runs the training.
    """
    print(f"--- Step 3: Loading Model ({MODEL_NAME}) ---")
    
    # Load the model for sequence classification
    model = BioGptForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
        pad_token_id=tokenizer.eos_token_id # Set pad token
    )
    
    # Define Training Arguments
    # These can be tuned for better performance
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,           # 3 epochs is a good start
        learning_rate=2e-5,           # Standard learning rate for fine-tuning
        per_device_train_batch_size=4,# Lower this if you get "Out of Memory" errors
        per_device_eval_batch_size=4,
        weight_decay=0.01,
        eval_strategy="epoch",  # Evaluate at the end of each epoch
        save_strategy="epoch",
        logging_strategy="steps", # Log training loss at steps
        logging_steps=10,         # Log every 10 steps
        load_best_model_at_end=True,  # Saves the best model
        metric_for_best_model="f1_macro",
        push_to_hub=False,
    )
    
    # Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_test,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("--- Step 4: Starting Model Training ---")
    print("This may take a while depending on your data size and GPU...")
    trainer.train()
    
    print("--- Training Complete ---")
    
    # Save the final best model
    trainer.save_model(f"{OUTPUT_DIR}/best_model")
    print(f"Best model saved to {OUTPUT_DIR}/best_model")
    
    return trainer

def evaluate_and_predict(trainer, test_df, tokenized_test, id2label):
    """
    Evaluates the model and shows example predictions.
    """
    print("--- Step 5: Evaluating Model on Test Set ---")
    
    # Get final metrics from the test set
    eval_results = trainer.evaluate()
    print("\n--- Final Test Set Metrics ---")
    for key, value in eval_results.items():
        print(f"{key}: {value:.4f}")
        
    # --- Show Predictions ---
    print("\n--- Example Predictions ---")
    
    # Get model outputs (logits)
    predictions = trainer.predict(tokenized_test)
    raw_scores = predictions.predictions
    
    # Get the predicted class ID (the one with the highest score)
    predicted_label_ids = np.argmax(raw_scores, axis=1)
    
    # Map IDs back to original BI-RADS labels
    predicted_labels = [id2label[label_id] for label_id in predicted_label_ids]
    
    # Add predictions to our original test DataFrame
    # Note: test_df was created with .copy(), so this is safe
    test_df['predicted_label_id'] = predicted_label_ids
    test_df['predicted_birads'] = predicted_labels
    
    # Display the first 10 predictions
    print("Showing first 10 test predictions:")
    print(test_df[['text', TARGET_COLUMN, 'predicted_birads']].head(10))

    # Show a full example
    print("\n--- Detailed First Prediction ---")
    print(f"Text: {test_df.iloc[0]['text'][:500]}...")
    print(f"Actual BI-RADS:   {test_df.iloc[0][TARGET_COLUMN]}")
    print(f"Predicted BI-RADS: {test_df.iloc[0]['predicted_birads']}")


def main():
    # Step 1: Load and process data
    df, label2id, id2label, num_labels = load_and_preprocess_data()
    
    # Split into training and testing sets
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df['label'] # Ensures class balance in splits
    )
    
    # Step 2: Tokenize
    tokenized_train, tokenized_test, tokenizer = tokenize_data(
        train_df.copy(), test_df.copy()
    )
    
    # Step 3 & 4: Train
    trainer = train_model(
        tokenized_train, 
        tokenized_test, 
        tokenizer, 
        num_labels, 
        id2label, 
        label2id
    )
    
    # Step 5: Evaluate and show predictions
    evaluate_and_predict(trainer, test_df.copy(), tokenized_test, id2label)

if __name__ == "__main__":
    main()