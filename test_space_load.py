from transformers import AutoTokenizer, BioGptForSequenceClassification
import torch

MODEL_REPO = "ishro/biogpt-aura"

print(f"Loading model from {MODEL_REPO}...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO)
    print("Tokenizer loaded.")
    model = BioGptForSequenceClassification.from_pretrained(MODEL_REPO)
    print("Model loaded.")
    model.eval()
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
