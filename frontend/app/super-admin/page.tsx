"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AuraLogo } from "@/components/aura-logo"
import { FileText, RefreshCw, Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/contexts/AuthContext"
import { listDocuments, getDocument, getParsedText, getStructuredData, getRiskPrediction } from "@/lib/documentApi"
import type { DocumentStatus, PredictionResult } from "@/lib/types"

interface PipelineData {
  document: DocumentStatus | null
  parsedText: string | null
  structuredData: any | null
  prediction: PredictionResult | null
}

export default function SuperAdminPage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [documents, setDocuments] = useState<DocumentStatus[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string>("")
  const [pipelineData, setPipelineData] = useState<PipelineData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>("")

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await listDocuments(1, 100)
      // Filter to only show documents that are at least parsed
      const processedDocs = response.documents.filter(
        doc => doc.status !== "pending" && doc.status !== "uploaded"
      )
      setDocuments(processedDocs)
    } catch (err) {
      console.error("Failed to load documents:", err)
      setError("Failed to load documents")
    }
  }

  const fetchPipelineData = async (documentId: string) => {
    setIsLoading(true)
    setError("")
    setPipelineData(null)

    try {
      // Fetch all pipeline data in parallel
      const [document, parsedText, structuredData, prediction] = await Promise.allSettled([
        getDocument(documentId),
        getParsedText(documentId),
        getStructuredData(documentId),
        getRiskPrediction(documentId)
      ])

      setPipelineData({
        document: document.status === "fulfilled" ? document.value : null,
        parsedText: parsedText.status === "fulfilled" ? parsedText.value.parsed_text : null,
        structuredData: structuredData.status === "fulfilled" ? structuredData.value.structured_data : null,
        prediction: prediction.status === "fulfilled" ? prediction.value : null
      })
    } catch (err) {
      console.error("Failed to fetch pipeline data:", err)
      setError(err instanceof Error ? err.message : "Failed to fetch pipeline data")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDocumentSelect = (documentId: string) => {
    setSelectedDocId(documentId)
    fetchPipelineData(documentId)
  }

  const getRiskBadgeClass = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
      case "medium":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200"
      case "low":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
    }
  }

  const getStepStatus = (step: string) => {
    if (!pipelineData) return "pending"
    
    switch (step) {
      case "ingestion":
        return pipelineData.document ? "completed" : "pending"
      case "parsing":
        return pipelineData.parsedText ? "completed" : "pending"
      case "structuring":
        return pipelineData.structuredData ? "completed" : "pending"
      case "prediction":
        return pipelineData.prediction ? "completed" : "pending"
      default:
        return "pending"
    }
  }

  return (
    <ProtectedRoute allowedRoles={["super_admin"]}>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 dark:from-gray-900 dark:via-purple-950 dark:to-blue-950">
        {/* Header */}
        <div className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <AuraLogo className="h-8 w-8" />
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent">
                    Super Admin Portal
                  </h1>
                  <p className="text-sm text-muted-foreground">Pipeline Visualization & System Monitoring</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ThemeToggle />
                <div className="text-sm text-right">
                  <p className="font-medium">{user?.full_name}</p>
                  <p className="text-muted-foreground">{user?.organization}</p>
                </div>
                <Button variant="outline" onClick={logout} className="glow-secondary">
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="container mx-auto px-6 py-8">
          {/* Document Selector */}
          <Card className="mb-8 glow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Select Document for Pipeline Visualization
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">Document</label>
                  <Select value={selectedDocId} onValueChange={handleDocumentSelect}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a document to view pipeline" />
                    </SelectTrigger>
                    <SelectContent>
                      {documents.map((doc) => (
                        <SelectItem key={doc.upload_id} value={doc.upload_id}>
                          {doc.file_info.filename} - {doc.clinic || "Unknown Clinic"}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  onClick={() => selectedDocId && fetchPipelineData(selectedDocId)}
                  disabled={!selectedDocId || isLoading}
                  className="glow-primary"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh Data
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* API Endpoints Overview */}
          {selectedDocId && !isLoading && (
            <Card className="mb-8 glow-card bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-950">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  API Endpoints Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Document Ingestion */}
                  <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-blue-800">
                    <h4 className="text-sm font-semibold mb-2 text-blue-700 dark:text-blue-400">Document Ingestion (8001)</h4>
                    <div className="space-y-1 text-xs font-mono">
                      <div><span className="text-blue-600">POST</span> /documents/upload</div>
                      <div><span className="text-green-600">GET</span> /documents/{`{id}`}</div>
                      <div><span className="text-green-600">GET</span> /documents/</div>
                    </div>
                  </div>

                  {/* Document Parsing */}
                  <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-purple-200 dark:border-purple-800">
                    <h4 className="text-sm font-semibold mb-2 text-purple-700 dark:text-purple-400">Document Parsing (8002)</h4>
                    <div className="space-y-1 text-xs font-mono">
                      <div><span className="text-blue-600">POST</span> /parsing/parse</div>
                      <div><span className="text-green-600">GET</span> /parsing/result/document/{`{id}`}</div>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">Tool: Docling OCR</div>
                  </div>

                  {/* Information Structuring */}
                  <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-amber-200 dark:border-amber-800">
                    <h4 className="text-sm font-semibold mb-2 text-amber-700 dark:text-amber-400">Information Structuring (8003)</h4>
                    <div className="space-y-1 text-xs font-mono">
                      <div><span className="text-blue-600">POST</span> /structuring/structure</div>
                      <div><span className="text-green-600">GET</span> /structuring/result/document/{`{id}`}</div>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">AI: Gemini 1.5 Flash</div>
                  </div>

                  {/* Risk Prediction */}
                  <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-red-200 dark:border-red-800">
                    <h4 className="text-sm font-semibold mb-2 text-red-700 dark:text-red-400">Risk Prediction (8004)</h4>
                    <div className="space-y-1 text-xs font-mono">
                      <div><span className="text-blue-600">POST</span> /predictions/predict</div>
                      <div><span className="text-green-600">GET</span> /predictions/document/{`{id}`}</div>
                      <div><span className="text-orange-600">PATCH</span> /predictions/{`{id}`}/review</div>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">Model: BioGPT (microsoft/biogpt)</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Message */}
          {error && (
            <Card className="mb-8 border-red-500">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-5 w-5" />
                  <p>{error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Loading State */}
          {isLoading && (
            <Card className="glow-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center gap-3 py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading pipeline data...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pipeline Visualization */}
          {!isLoading && pipelineData && (
            <div className="grid grid-cols-1 gap-6">
              {/* Step 1: Document Ingestion */}
              <Card className={`glow-card ${getStepStatus("ingestion") === "completed" ? "border-green-500" : ""}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {getStepStatus("ingestion") === "completed" ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <span>Step 1: Document Ingestion</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* API Endpoint Info */}
                  <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md border border-blue-200 dark:border-blue-800">
                    <div className="text-xs font-mono space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-blue-700 dark:text-blue-400">POST</span>
                        <span className="text-blue-600 dark:text-blue-300">/documents/upload</span>
                        <span className="text-muted-foreground ml-auto">Upload file</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-green-700 dark:text-green-400">GET</span>
                        <span className="text-green-600 dark:text-green-300">/documents/{`{document_id}`}</span>
                        <span className="text-muted-foreground ml-auto">Retrieve metadata</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Service: <span className="font-medium">document-ingestion</span> (Port 8001)
                      </div>
                    </div>
                  </div>

                  {pipelineData.document ? (
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Filename:</span> {pipelineData.document.file_info.filename}
                        </div>
                        <div>
                          <span className="font-medium">Size:</span> {(pipelineData.document.file_info.size / 1024).toFixed(2)} KB
                        </div>
                        <div>
                          <span className="font-medium">Clinic:</span> {pipelineData.document.clinic || "Unknown"}
                        </div>
                        <div>
                          <span className="font-medium">Status:</span> {pipelineData.document.status}
                        </div>
                      </div>
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-medium text-primary">View JSON Response</summary>
                        <pre className="mt-2 p-4 bg-muted rounded-md text-xs overflow-x-auto">
                          {JSON.stringify(pipelineData.document, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No document data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 2: Document Parsing (Docling OCR) */}
              <Card className={`glow-card ${getStepStatus("parsing") === "completed" ? "border-green-500" : ""}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {getStepStatus("parsing") === "completed" ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <span>Step 2: Document Parsing (Docling OCR)</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* API Endpoint Info */}
                  <div className="mb-4 p-3 bg-purple-50 dark:bg-purple-950/30 rounded-md border border-purple-200 dark:border-purple-800">
                    <div className="text-xs font-mono space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-blue-700 dark:text-blue-400">POST</span>
                        <span className="text-purple-600 dark:text-purple-300">/parsing/parse</span>
                        <span className="text-muted-foreground ml-auto">Parse document with Docling</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-green-700 dark:text-green-400">GET</span>
                        <span className="text-purple-600 dark:text-purple-300">/parsing/result/document/{`{document_id}`}</span>
                        <span className="text-muted-foreground ml-auto">Get extracted text</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Service: <span className="font-medium">document-parsing</span> (Port 8002) | Tool: <span className="font-medium">Docling OCR</span>
                      </div>
                    </div>
                  </div>

                  {pipelineData.parsedText ? (
                    <div className="space-y-2">
                      <div className="text-sm mb-2">
                        <span className="font-medium">Extracted Text Length:</span> {pipelineData.parsedText.length} characters
                      </div>
                      <div className="p-4 bg-muted rounded-md text-sm max-h-64 overflow-y-auto">
                        {pipelineData.parsedText}
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No parsed text available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 3: Information Structuring (Gemini) */}
              <Card className={`glow-card ${getStepStatus("structuring") === "completed" ? "border-green-500" : ""}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {getStepStatus("structuring") === "completed" ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <span>Step 3: Information Structuring (Gemini AI)</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* API Endpoint Info */}
                  <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-md border border-amber-200 dark:border-amber-800">
                    <div className="text-xs font-mono space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-blue-700 dark:text-blue-400">POST</span>
                        <span className="text-amber-600 dark:text-amber-300">/structuring/structure</span>
                        <span className="text-muted-foreground ml-auto">Extract structured data</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-green-700 dark:text-green-400">GET</span>
                        <span className="text-amber-600 dark:text-amber-300">/structuring/result/document/{`{document_id}`}</span>
                        <span className="text-muted-foreground ml-auto">Get structured fields</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Service: <span className="font-medium">information-structuring</span> (Port 8003) | AI: <span className="font-medium">Gemini 1.5 Flash</span>
                      </div>
                    </div>
                  </div>

                  {pipelineData.structuredData ? (
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {Object.entries(pipelineData.structuredData).map(([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key.replace(/_/g, ' ').toUpperCase()}:</span>{' '}
                            {typeof value === 'string' ? value : JSON.stringify(value)}
                          </div>
                        ))}
                      </div>
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-medium text-primary">View JSON Response</summary>
                        <pre className="mt-2 p-4 bg-muted rounded-md text-xs overflow-x-auto">
                          {JSON.stringify(pipelineData.structuredData, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No structured data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 4: Risk Prediction (BioGPT) */}
              <Card className={`glow-card ${getStepStatus("prediction") === "completed" ? "border-green-500" : ""}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {getStepStatus("prediction") === "completed" ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <span>Step 4: Risk Prediction (BioGPT Model)</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* API Endpoint Info */}
                  <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 rounded-md border border-red-200 dark:border-red-800">
                    <div className="text-xs font-mono space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-blue-700 dark:text-blue-400">POST</span>
                        <span className="text-red-600 dark:text-red-300">/predictions/predict</span>
                        <span className="text-muted-foreground ml-auto">Generate BI-RADS prediction</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-green-700 dark:text-green-400">GET</span>
                        <span className="text-red-600 dark:text-red-300">/predictions/document/{`{document_id}`}</span>
                        <span className="text-muted-foreground ml-auto">Get prediction result</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-orange-700 dark:text-orange-400">PATCH</span>
                        <span className="text-red-600 dark:text-red-300">/predictions/{`{prediction_id}`}/review</span>
                        <span className="text-muted-foreground ml-auto">Update review status</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Service: <span className="font-medium">risk-prediction</span> (Port 8004) | Model: <span className="font-medium">BioGPT (microsoft/biogpt)</span>
                      </div>
                    </div>
                  </div>

                  {pipelineData.prediction ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm font-medium">Predicted BI-RADS:</span>
                          <div className="text-2xl font-bold">{pipelineData.prediction.predicted_birads}</div>
                        </div>
                        <div>
                          <span className="text-sm font-medium">Risk Level:</span>
                          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRiskBadgeClass(pipelineData.prediction.risk_level)}`}>
                            {pipelineData.prediction.risk_level?.toUpperCase()}
                          </div>
                        </div>
                      </div>
                      
                      {pipelineData.prediction.probabilities && (
                        <div>
                          <h4 className="text-sm font-medium mb-2">Class Probabilities</h4>
                          <div className="space-y-2">
                            {Object.entries(pipelineData.prediction.probabilities).map(([cls, prob]) => (
                              <div key={cls} className="flex items-center gap-2">
                                <span className="text-sm w-20">BI-RADS {cls}:</span>
                                <div className="flex-1 bg-muted rounded-full h-6">
                                  <div 
                                    className="bg-primary h-6 rounded-full flex items-center justify-end px-2"
                                    style={{ width: `${(prob as number) * 100}%` }}
                                  >
                                    <span className="text-xs text-primary-foreground font-medium">
                                      {((prob as number) * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-medium text-primary">View JSON Response</summary>
                        <pre className="mt-2 p-4 bg-muted rounded-md text-xs overflow-x-auto">
                          {JSON.stringify(pipelineData.prediction, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No prediction data available</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !pipelineData && !error && (
            <Card className="glow-card">
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">No Document Selected</h3>
                  <p className="text-muted-foreground">
                    Select a document from the dropdown above to visualize the complete pipeline
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}
