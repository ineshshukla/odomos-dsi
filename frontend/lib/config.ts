// API Configuration
export const API_CONFIG = {
  AUTH_SERVICE: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8010',
  DOCUMENT_INGESTION: process.env.NEXT_PUBLIC_INGESTION_SERVICE_URL || 'http://localhost:8001',
  DOCUMENT_PARSING: process.env.NEXT_PUBLIC_PARSING_SERVICE_URL || 'http://localhost:8002',
  INFORMATION_STRUCTURING: process.env.NEXT_PUBLIC_STRUCTURING_SERVICE_URL || 'http://localhost:8003',
  RISK_PREDICTION: process.env.NEXT_PUBLIC_RISK_PREDICTION_URL || 'http://localhost:8004',
  API_BASE: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
}

// Local Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
}

// Application Constants
export const APP_CONFIG = {
  APP_NAME: 'Odomos DSI',
  APP_DESCRIPTION: 'Mammography Report Analysis System',
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: ['application/pdf', 'image/jpeg', 'image/png'],
}
