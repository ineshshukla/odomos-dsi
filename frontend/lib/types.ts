// User Types
export interface User {
  id: string
  email: string
  full_name: string
  organization: string
  role: 'clinic_admin' | 'gcf_coordinator' | 'super_admin'
  is_active: boolean
  created_at: string
  updated_at: string
}

// Authentication Types
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
  organization: string
  role: 'clinic_admin' | 'gcf_coordinator' | 'super_admin'
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  user: User
  token: Token
}

// Document Types
export interface Document {
  id: string
  filename: string
  file_path: string
  file_size: number
  file_type: string
  upload_status: 'pending' | 'processing' | 'completed' | 'failed'
  uploaded_by: string
  uploaded_at: string
  processed_at?: string
  error_message?: string
}

export interface DocumentStatus {
  upload_id: string
  filename?: string  // For backward compatibility
  file_info: {
    filename: string
    size: number
    content_type: string
  }
  created_at: string
  updated_at?: string
  status: 'pending' | 'processing' | 'uploaded' | 'parsed' | 'structured' | 'predicted' | 'failed'
  clinic?: string
  clinic_name?: string
  upload_timestamp?: string
  error?: string
}

export interface UploadDocumentResponse {
  upload_id: string
  status: string
  file_info: {
    filename: string
    size: number
    content_type: string
  }
  created_at: string
  message: string
}

export interface ListDocumentsResponse {
  documents: DocumentStatus[]
  total: number
  page: number
  page_size: number
}

// Report Types
export interface Report {
  id: string
  document_id: string
  patient_id?: string
  report_date?: string
  findings: string
  impression: string
  birads_category?: string
  recommendations?: string
  created_at: string
  updated_at: string
}

// Patient Types
export interface Patient {
  id: string
  name: string
  age?: number
  mrn?: string
  clinic_id: string
  created_at: string
  updated_at: string
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Form Types
export interface UploadFormData {
  file: File
  patient_id?: string
  clinic_id?: string
}

// Risk Prediction Types
export interface PredictionResult {
  prediction_id: string
  document_id: string
  structuring_id?: string
  predicted_birads: string
  predicted_label_id: number
  confidence_score: number
  probabilities: Record<string, number>
  risk_level: 'high' | 'medium' | 'low' | 'needs_assessment' | 'unknown'
  review_status?: string
  coordinator_notes?: string
  reviewed_by?: string
  reviewed_at?: string
  model_version: string
  processing_time?: number
  status: string
  created_at: string
}
