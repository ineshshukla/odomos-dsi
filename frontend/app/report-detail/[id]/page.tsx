"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { AuraLogo } from "@/components/aura-logo"
import { ArrowLeft, FileText, AlertTriangle, Loader2, Download, CheckCircle2 } from "lucide-react"
import { useRouter, useParams } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/contexts/AuthContext"
import { getDocument, getRiskPrediction, getParsedText, getStructuredData, updateReviewStatus } from "@/lib/documentApi"
import type { DocumentStatus, PredictionResult } from "@/lib/types"

interface ReportData {
  document: DocumentStatus | null
  prediction: PredictionResult | null
  parsedText: string | null
  structuredData: any | null
  reviewStatus: "New" | "Under Review" | "Follow-up Initiated" | "Review Complete"
  internalNotes: string
}

export default function ReportDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user, logout } = useAuth()
  const [report, setReport] = useState<ReportData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string>("")
  const [reviewStatus, setReviewStatus] = useState<"New" | "Under Review" | "Follow-up Initiated" | "Review Complete">("New")
  const [internalNotes, setInternalNotes] = useState("")
  const [showSaveConfirmation, setShowSaveConfirmation] = useState(false)

  useEffect(() => {
    loadReportDetails()
  }, [params.id])

  const loadReportDetails = async () => {
    setIsLoading(true)
    setError("")
    
    try {
      const documentId = params.id as string
      
      // Fetch all available data in parallel
      const [document, prediction, parsedText, structuredData] = await Promise.allSettled([
        getDocument(documentId),
        getRiskPrediction(documentId),
        getParsedText(documentId),
        getStructuredData(documentId)
      ])

      const reportData: ReportData = {
        document: document.status === 'fulfilled' ? document.value : null,
        prediction: prediction.status === 'fulfilled' ? prediction.value : null,
        parsedText: parsedText.status === 'fulfilled' ? parsedText.value.parsed_text : null,
        structuredData: structuredData.status === 'fulfilled' ? structuredData.value.structured_data : null,
        reviewStatus: prediction.status === 'fulfilled' && prediction.value.review_status 
          ? prediction.value.review_status as any
          : "New",
        internalNotes: prediction.status === 'fulfilled' && prediction.value.coordinator_notes 
          ? prediction.value.coordinator_notes 
          : ""
      }

      console.log("📊 Report Data loaded:", {
        hasDocument: !!reportData.document,
        hasPrediction: !!reportData.prediction,
        hasParsedText: !!reportData.parsedText,
        hasStructuredData: !!reportData.structuredData,
        structuredData: reportData.structuredData
      })

      setReport(reportData)
      setReviewStatus(reportData.reviewStatus)
      setInternalNotes(reportData.internalNotes)
      
    } catch (err) {
      console.error("Failed to load report details:", err)
      setError(err instanceof Error ? err.message : "Failed to load report details")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveChanges = async () => {
    if (!report?.document) return
    
    try {
      setIsLoading(true)
      setError("")
      
      // Call the API to update review status
      const updatedPrediction = await updateReviewStatus(
        report.document.upload_id,
        reviewStatus,
        internalNotes
      )
      
      // Update local state with the response
      setReport({
        ...report,
        prediction: updatedPrediction,
        reviewStatus: reviewStatus,
        internalNotes: internalNotes
      })
      
      setShowSaveConfirmation(true)
      setTimeout(() => setShowSaveConfirmation(false), 3000)
      
      // Update localStorage to notify dashboard
      localStorage.setItem("updatedReport", JSON.stringify({
        id: report.document.upload_id,
        reviewStatus
      }))
      window.dispatchEvent(new Event("storage"))
      
    } catch (err) {
      console.error("Failed to save changes:", err)
      setError(err instanceof Error ? err.message : "Failed to save changes")
    } finally {
      setIsLoading(false)
    }
  }

  const handleBackToDashboard = () => {
    router.push("/gcf-dashboard")
  }

  const getRiskBadgeClass = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "high":
        return "risk-high px-3 py-1 rounded-full text-sm font-medium"
      case "medium":
        return "risk-medium px-3 py-1 rounded-full text-sm font-medium"
      case "low":
        return "risk-low px-3 py-1 rounded-full text-sm font-medium"
      default:
        return "bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium dark:bg-gray-800 dark:text-gray-200"
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="absolute inset-0 dark:bg-gradient-to-br dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 pointer-events-none" />
        <div className="text-center relative z-10">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading report details...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="absolute inset-0 dark:bg-gradient-to-br dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 pointer-events-none" />
        <div className="text-center relative z-10">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <p className="text-lg font-medium text-foreground mb-2">Failed to Load Report</p>
          <p className="text-muted-foreground mb-4">{error || "Report not found"}</p>
          <Button onClick={() => router.push("/gcf-dashboard")}>Back to Dashboard</Button>
        </div>
      </div>
    )
  }

  const riskLevel = report.prediction?.risk_level || "pending"
  const birads = report.prediction?.predicted_birads || "N/A"
  const confidence = report.prediction?.confidence_score || 0

  return (
    <ProtectedRoute allowedRoles={['gcf_coordinator']}>
    <div className="min-h-screen bg-background">
      {/* Gradient background for dark theme */}
      <div className="absolute inset-0 dark:bg-gradient-to-br dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 pointer-events-none" />

      {/* Header */}
      <header className="bg-card border-b border-border relative z-10 dark:bg-card/80 dark:backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <AuraLogo />
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <div className="text-right">
                <p className="text-sm font-medium text-foreground">{user?.full_name || "GCF Coordinator"}</p>
                <p className="text-xs text-muted-foreground">{user?.organization || "GCF Program"}</p>
              </div>
              <Button
                variant="outline"
                onClick={logout}
                className="text-primary border-primary hover:bg-primary hover:text-primary-foreground glow-primary"
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Summary Bar */}
      <div className="bg-card border-b border-border relative z-10 dark:bg-card/80 dark:backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={handleBackToDashboard}
                className="flex items-center gap-2 text-primary hover:bg-primary/10 glow-primary"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </Button>
              <div className="h-6 w-px bg-border"></div>
              <div className="flex items-center gap-6">
                <div>
                  <span className="text-sm text-muted-foreground">Document:</span>
                  <span className="ml-2 font-medium text-foreground">{report.document?.file_info.filename}</span>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Clinic:</span>
                  <span className="ml-2 font-medium text-foreground">{report.document?.clinic_name || "Unknown"}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className={getRiskBadgeClass(riskLevel)}>{riskLevel.toUpperCase()} Risk</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Report Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Document Info Card */}
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-foreground">
                  <FileText className="w-5 h-5" />
                  Document Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Document ID</p>
                    <p className="font-mono text-sm text-foreground">{report.document?.upload_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Upload Date</p>
                    <p className="text-sm text-foreground">{new Date(report.document?.created_at || '').toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">File Size</p>
                    <p className="text-sm text-foreground">{(report.document?.file_info.size || 0 / 1024).toFixed(2)} KB</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <p className="text-sm text-foreground capitalize">{report.document?.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Parsed Text Card */}
            {report.parsedText && (
              <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-foreground">Extracted Text</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <div className="whitespace-pre-wrap text-sm text-foreground font-mono leading-relaxed">{report.parsedText}</div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Structured Data Card */}
            {report.structuredData && (
              <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-foreground">Structured Medical Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Patient Information */}
                  <div>
                    <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Patient Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {report.structuredData.age && report.structuredData.age !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Age</p>
                          <p className="text-sm text-foreground">{report.structuredData.age}</p>
                        </div>
                      )}
                      {report.structuredData.children && report.structuredData.children !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Children</p>
                          <p className="text-sm text-foreground">{report.structuredData.children}</p>
                        </div>
                      )}
                      {report.structuredData.lmp && report.structuredData.lmp !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Last Menstrual Period</p>
                          <p className="text-sm text-foreground">{report.structuredData.lmp}</p>
                        </div>
                      )}
                      {report.structuredData.hormonal_therapy && report.structuredData.hormonal_therapy !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Hormonal Therapy</p>
                          <p className="text-sm text-foreground">{report.structuredData.hormonal_therapy}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Clinical Information */}
                  <div>
                    <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Clinical Information</h3>
                    <div className="space-y-3">
                      {report.structuredData.medical_unit && report.structuredData.medical_unit !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Medical Unit</p>
                          <p className="text-sm text-foreground">{report.structuredData.medical_unit}</p>
                        </div>
                      )}
                      {report.structuredData.reason && report.structuredData.reason !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Reason for Examination</p>
                          <p className="text-sm text-foreground">{report.structuredData.reason}</p>
                        </div>
                      )}
                      {report.structuredData.family_history && report.structuredData.family_history !== "unknown" && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Family History</p>
                          <p className="text-sm text-foreground">{report.structuredData.family_history}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Observations */}
                  {report.structuredData.observations && report.structuredData.observations !== "unknown" && (
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Observations</h3>
                      <p className="text-sm text-foreground whitespace-pre-wrap">{report.structuredData.observations}</p>
                    </div>
                  )}

                  {/* Conclusion */}
                  {report.structuredData.conclusion && report.structuredData.conclusion !== "unknown" && (
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Conclusion</h3>
                      <p className="text-sm text-foreground whitespace-pre-wrap">{report.structuredData.conclusion}</p>
                    </div>
                  )}

                  {/* Recommendations */}
                  {report.structuredData.recommendations && report.structuredData.recommendations !== "unknown" && (
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Recommendations</h3>
                      <p className="text-sm text-foreground whitespace-pre-wrap">{report.structuredData.recommendations}</p>
                    </div>
                  )}

                  {/* Original BI-RADS */}
                  {report.structuredData.birads && report.structuredData.birads !== "unknown" && (
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-3 border-b border-border pb-2">Original Assessment</h3>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Original BI-RADS Score</p>
                        <p className="text-lg text-foreground font-bold">BI-RADS {report.structuredData.birads}</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Risk Assessment & Review */}
          <div className="space-y-6">
            {/* AI Risk Assessment Card */}
            {report.prediction && (
              <Card className="card-glow border-primary/20 dark:bg-card/80 dark:backdrop-blur-sm">
                <CardHeader className="bg-primary/5">
                  <CardTitle className="flex items-center gap-2 text-foreground">
                    <AlertTriangle className="w-5 h-5 text-primary" />
                    AI Risk Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Predicted BI-RADS Category</p>
                    <p className="text-2xl font-bold text-foreground">BI-RADS {birads}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Risk Level</p>
                    <span className={getRiskBadgeClass(riskLevel)}>{riskLevel.toUpperCase()}</span>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Confidence Score</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full transition-all" 
                          style={{ width: `${confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-foreground">{(confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  {report.prediction.probabilities && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">BI-RADS Probabilities</p>
                      <div className="space-y-2">
                        {Object.entries(report.prediction.probabilities).map(([category, prob]) => (
                          <div key={category} className="flex justify-between items-center text-sm">
                            <span className="text-foreground">BI-RADS {category}</span>
                            <span className="text-muted-foreground">{((prob as number) * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="pt-4 border-t border-border">
                    <p className="text-xs text-muted-foreground">
                      Model: BioGPT v{report.prediction.model_version}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Analyzed: {new Date(report.prediction.created_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Review Status Card */}
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-foreground">Coordinator Review</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {report.prediction?.reviewed_at && (
                  <div className="bg-muted/30 p-3 rounded-lg text-sm">
                    <p className="text-muted-foreground">Last reviewed:</p>
                    <p className="text-foreground font-medium">{new Date(report.prediction.reviewed_at).toLocaleString()}</p>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium text-foreground mb-2 block">Review Status</label>
                  <Select 
                    value={reviewStatus} 
                    onValueChange={(value) => setReviewStatus(value as any)}
                  >
                    <SelectTrigger className="dark:bg-muted/50 dark:border-primary/30">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="dark:bg-card dark:border-primary/30">
                      <SelectItem value="New">New</SelectItem>
                      <SelectItem value="Under Review">Under Review</SelectItem>
                      <SelectItem value="Follow-up Initiated">Follow-up Initiated</SelectItem>
                      <SelectItem value="Review Complete">Review Complete</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium text-foreground mb-2 block">Internal Notes</label>
                  <Textarea
                    value={internalNotes}
                    onChange={(e) => setInternalNotes(e.target.value)}
                    placeholder="Add your review notes here..."
                    className="min-h-32 dark:bg-muted/50 dark:border-primary/30"
                  />
                </div>

                <Button
                  onClick={handleSaveChanges}
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-primary"
                >
                  Save Changes
                </Button>

                {showSaveConfirmation && (
                  <div className="flex items-center gap-2 text-sm text-success bg-success/10 p-3 rounded-lg">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Changes saved successfully</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
