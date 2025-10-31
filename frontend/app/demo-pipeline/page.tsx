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

export default function DemoPipelinePage() {
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
    <ProtectedRoute allowedRoles={['clinic_admin', 'gcf_coordinator']}>
      <div className="min-h-screen bg-background">
        {/* Gradient overlay for dark mode */}
        <div className="absolute inset-0 dark:bg-gradient-to-br dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 pointer-events-none" />

        {/* Header */}
        <div className="border-b border-border/40 bg-background/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <AuraLogo className="w-10 h-10" />
                <div>
                  <h1 className="text-2xl font-bold text-foreground">Pipeline Demo</h1>
                  <p className="text-sm text-muted-foreground">View processing steps for uploaded documents</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ThemeToggle />
                <Button
                  variant="outline"
                  onClick={() => router.push("/gcf-dashboard")}
                  className="glow-primary"
                >
                  Back to Dashboard
                </Button>
                <Button
                  variant="ghost"
                  onClick={logout}
                  className="text-muted-foreground hover:text-foreground"
                >
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
          {/* Document Selector */}
          <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm mb-6">
            <CardHeader>
              <CardTitle className="text-foreground flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Select Document
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 items-center">
                <Select value={selectedDocId} onValueChange={handleDocumentSelect}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Choose a document to view pipeline data..." />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((doc) => (
                      <SelectItem key={doc.upload_id} value={doc.upload_id}>
                        {doc.file_info.filename} - {doc.status} ({new Date(doc.created_at).toLocaleDateString()})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={loadDocuments}
                  variant="outline"
                  className="gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </Button>
              </div>
            </CardContent>
          </Card>

          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="animate-spin h-8 w-8 text-primary" />
              <span className="ml-3 text-muted-foreground">Loading pipeline data...</span>
            </div>
          )}

          {error && (
            <Card className="card-glow border-red-500 dark:bg-card/80 dark:backdrop-blur-sm mb-6">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {pipelineData && !isLoading && (
            <div className="space-y-6">
              {/* Step 1: Document Ingestion */}
              <Card className={`card-glow dark:bg-card/80 dark:backdrop-blur-sm ${
                getStepStatus("ingestion") === "completed" ? "border-l-4 border-l-green-500" : ""
              }`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        1
                      </div>
                      Document Ingestion
                    </CardTitle>
                    {getStepStatus("ingestion") === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">POST /documents/upload</p>
                </CardHeader>
                <CardContent>
                  {pipelineData.document ? (
                    <div className="bg-muted/50 rounded-lg p-4">
                      <pre className="text-sm overflow-x-auto">
                        {JSON.stringify({
                          upload_id: pipelineData.document.upload_id,
                          filename: pipelineData.document.file_info.filename,
                          size: pipelineData.document.file_info.size,
                          content_type: pipelineData.document.file_info.content_type,
                          status: pipelineData.document.status,
                          clinic_name: pipelineData.document.clinic_name,
                          created_at: pipelineData.document.created_at,
                          updated_at: pipelineData.document.updated_at
                        }, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 2: Document Parsing */}
              <Card className={`card-glow dark:bg-card/80 dark:backdrop-blur-sm ${
                getStepStatus("parsing") === "completed" ? "border-l-4 border-l-green-500" : ""
              }`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        2
                      </div>
                      Document Parsing (Docling OCR)
                    </CardTitle>
                    {getStepStatus("parsing") === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">POST /parsing/parse-internal</p>
                </CardHeader>
                <CardContent>
                  {pipelineData.parsedText ? (
                    <div className="bg-muted/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <div className="mb-2 text-sm text-muted-foreground">
                        Extracted Text Length: {pipelineData.parsedText.length} characters
                      </div>
                      <pre className="text-sm whitespace-pre-wrap">
                        {pipelineData.parsedText}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 3: Information Structuring */}
              <Card className={`card-glow dark:bg-card/80 dark:backdrop-blur-sm ${
                getStepStatus("structuring") === "completed" ? "border-l-4 border-l-green-500" : ""
              }`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        3
                      </div>
                      Information Structuring (Gemini AI)
                    </CardTitle>
                    {getStepStatus("structuring") === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">POST /structuring/structure-internal</p>
                </CardHeader>
                <CardContent>
                  {pipelineData.structuredData ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(pipelineData.structuredData).map(([key, value]) => (
                          value !== "unknown" && (
                            <div key={key} className="bg-muted/50 rounded-lg p-3">
                              <div className="text-sm font-medium text-primary capitalize mb-1">
                                {key.replace(/_/g, " ")}
                              </div>
                              <div className="text-sm text-foreground">
                                {typeof value === "string" && value.length > 100
                                  ? value.substring(0, 100) + "..."
                                  : String(value)}
                              </div>
                            </div>
                          )
                        ))}
                      </div>
                      <details className="bg-muted/50 rounded-lg p-4">
                        <summary className="cursor-pointer text-sm font-medium text-primary mb-2">
                          View Full JSON
                        </summary>
                        <pre className="text-xs overflow-x-auto mt-2">
                          {JSON.stringify(pipelineData.structuredData, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Step 4: Risk Prediction */}
              <Card className={`card-glow dark:bg-card/80 dark:backdrop-blur-sm ${
                getStepStatus("prediction") === "completed" ? "border-l-4 border-l-green-500" : ""
              }`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        4
                      </div>
                      Risk Prediction (BioGPT)
                    </CardTitle>
                    {getStepStatus("prediction") === "completed" && (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">POST /predictions/predict-internal</p>
                </CardHeader>
                <CardContent>
                  {pipelineData.prediction ? (
                    <div className="space-y-4">
                      {/* Key Metrics */}
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground rounded-lg p-4 text-center">
                          <div className="text-3xl font-bold">BI-RADS {pipelineData.prediction.predicted_birads}</div>
                          <div className="text-sm opacity-90 mt-1">Predicted Category</div>
                        </div>
                        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4 text-center">
                          <div className="text-3xl font-bold">
                            {(pipelineData.prediction.confidence_score * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm opacity-90 mt-1">Confidence</div>
                        </div>
                        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold capitalize">
                            {pipelineData.prediction.risk_level}
                          </div>
                          <div className="text-sm opacity-90 mt-1">Risk Level</div>
                        </div>
                      </div>

                      {/* Probability Distribution */}
                      <div className="bg-muted/50 rounded-lg p-4">
                        <h4 className="font-medium text-foreground mb-3">Probability Distribution</h4>
                        <div className="space-y-2">
                          {Object.entries(pipelineData.prediction.probabilities).map(([birads, prob]) => (
                            <div key={birads} className="flex items-center gap-2">
                              <span className="text-sm font-medium w-20">BI-RADS {birads}:</span>
                              <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                                <div
                                  className="bg-primary h-full flex items-center justify-end pr-2 text-xs text-primary-foreground font-medium"
                                  style={{ width: `${(prob as number) * 100}%` }}
                                >
                                  {((prob as number) * 100).toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Full JSON */}
                      <details className="bg-muted/50 rounded-lg p-4">
                        <summary className="cursor-pointer text-sm font-medium text-primary mb-2">
                          View Full Prediction JSON
                        </summary>
                        <pre className="text-xs overflow-x-auto mt-2">
                          {JSON.stringify(pipelineData.prediction, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {!selectedDocId && !isLoading && (
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardContent className="py-20 text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-xl font-semibold text-foreground mb-2">Select a Document</h3>
                <p className="text-muted-foreground">
                  Choose a document from the dropdown above to view its complete pipeline processing data
                </p>
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </ProtectedRoute>
  )
}
