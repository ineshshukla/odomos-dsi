/**
 * Document API - Functions for interacting with the document services
 */

import { API_CONFIG, STORAGE_KEYS } from './config'
import type { UploadDocumentResponse, DocumentStatus, ListDocumentsResponse, PredictionResult } from './types'

/**
 * Get authorization headers with access token
 */
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
  return {
    'Authorization': `Bearer ${token}`,
  }
}

/**
 * Upload a document file
 */
export async function uploadDocument(file: File): Promise<UploadDocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_CONFIG.DOCUMENT_INGESTION}/documents/upload`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || error.message || 'Failed to upload document')
  }

  return response.json()
}

/**
 * List documents with pagination
 */
export async function listDocuments(
  page: number = 1,
  pageSize: number = 10
): Promise<ListDocumentsResponse> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_INGESTION}/documents/?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch documents' }))
    throw new Error(error.detail || error.message || 'Failed to fetch documents')
  }

  const data = await response.json()
  
  // Transform API response to frontend format
  const documents: DocumentStatus[] = (data.documents || []).map((doc: any) => ({
    upload_id: doc.upload_id || doc.id,
    file_info: {
      filename: doc.file_info?.filename || doc.filename || 'Unknown',
      size: doc.file_info?.size || doc.size || 0,
      content_type: doc.file_info?.content_type || doc.content_type || 'application/octet-stream',
    },
    created_at: doc.created_at || new Date().toISOString(),
    updated_at: doc.updated_at,
    status: mapDocumentStatus(doc.status),
    clinic: doc.organization || doc.clinic,
    error: doc.error_message || doc.error,
  }))

  return {
    documents,
    total: data.total || documents.length,
    page: data.page || page,
    page_size: data.limit || data.page_size || pageSize,
  }
}

/**
 * Map backend status to frontend status
 */
function mapDocumentStatus(status: string): DocumentStatus['status'] {
  switch (status?.toLowerCase()) {
    case 'pending':
      return 'pending'
    case 'processing':
      return 'processing'
    case 'completed':
    case 'uploaded':
      return 'uploaded'
    case 'parsed':
      return 'parsed'
    case 'structured':
      return 'structured'
    case 'failed':
    case 'error':
      return 'failed'
    default:
      return 'pending'
  }
}

/**
 * Get a specific document by ID
 */
export async function getDocument(documentId: string): Promise<DocumentStatus> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_INGESTION}/documents/${documentId}`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch document' }))
    throw new Error(error.detail || error.message || 'Failed to fetch document')
  }

  const doc = await response.json()
  
  return {
    upload_id: doc.upload_id || doc.id,
    file_info: {
      filename: doc.file_info?.filename || doc.filename || 'Unknown',
      size: doc.file_info?.size || doc.size || 0,
      content_type: doc.file_info?.content_type || doc.content_type || 'application/octet-stream',
    },
    created_at: doc.created_at || new Date().toISOString(),
    updated_at: doc.updated_at,
    status: mapDocumentStatus(doc.status),
    clinic: doc.organization || doc.clinic,
    error: doc.error_message || doc.error,
  }
}

/**
 * Delete a document
 */
export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_INGESTION}/documents/${documentId}`,
    {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete document' }))
    throw new Error(error.detail || error.message || 'Failed to delete document')
  }
}

/**
 * Get document processing status
 */
export async function getDocumentStatus(documentId: string): Promise<{
  status: string
  progress: number
  message?: string
}> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_INGESTION}/documents/${documentId}/status`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch status' }))
    throw new Error(error.detail || error.message || 'Failed to fetch status')
  }

  return response.json()
}

/**
 * Download a document
 */
export async function downloadDocument(documentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_INGESTION}/documents/${documentId}/download`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to download document' }))
    throw new Error(error.detail || error.message || 'Failed to download document')
  }

  return response.blob()
}

/**
 * Get risk prediction for a document
 */
export async function getRiskPrediction(documentId: string): Promise<PredictionResult> {
  const response = await fetch(
    `${API_CONFIG.RISK_PREDICTION}/predictions/document/${documentId}`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Prediction not found - document may still be processing')
    }
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch prediction' }))
    throw new Error(error.detail || error.message || 'Failed to fetch prediction')
  }

  return response.json()
}

/**
 * Get parsed text for a document
 */
export async function getParsedText(documentId: string): Promise<{
  document_id: string
  parsed_text: string
  extracted_at: string
}> {
  const response = await fetch(
    `${API_CONFIG.DOCUMENT_PARSING}/parsing/${documentId}`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Parsed text not found - document may still be processing')
    }
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch parsed text' }))
    throw new Error(error.detail || error.message || 'Failed to fetch parsed text')
  }

  return response.json()
}

/**
 * Get structured data for a document
 */
export async function getStructuredData(documentId: string): Promise<{
  id: string
  document_id: string
  structured_data: any
  status: string
  created_at: string
}> {
  const response = await fetch(
    `${API_CONFIG.INFORMATION_STRUCTURING}/structuring/result/document/${documentId}`,
    {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Structured data not found - document may still be processing')
    }
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch structured data' }))
    throw new Error(error.detail || error.message || 'Failed to fetch structured data')
  }

  return response.json()
}

/**
 * Update review status for a document
 */
export async function updateReviewStatus(
  documentId: string,
  reviewStatus: string,
  coordinatorNotes?: string
): Promise<PredictionResult> {
  const response = await fetch(
    `${API_CONFIG.RISK_PREDICTION}/predictions/document/${documentId}/review`,
    {
      method: 'PATCH',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        review_status: reviewStatus,
        coordinator_notes: coordinatorNotes || null,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update review status' }))
    throw new Error(error.detail || error.message || 'Failed to update review status')
  }

  return response.json()
}
