"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { AuraLogo } from "@/components/aura-logo"
import { ArrowLeft, FileText, AlertTriangle, Loader2, Download } from "lucide-react"
import { useRouter, useParams } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/contexts/AuthContext"
import { getDocument, getRiskPrediction, getParsedText, getStructuredData } from "@/lib/documentApi"
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
        reviewStatus: "New",
        internalNotes: ""
      }

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

  const handleSaveChanges = () => {
    if (report) {
      // Update the report status
      const updatedReport = {
        ...report,
        reviewStatus: reviewStatus as any,
        internalNotes: internalNotes,
      }

      setReport(updatedReport)

      localStorage.setItem(
        "updatedReport",
        JSON.stringify({
          id: report.id,
          reviewStatus: reviewStatus,
        }),
      )

      setShowSaveConfirmation(true)
      setTimeout(() => setShowSaveConfirmation(false), 3000)
    }
  }

  const handleBackToDashboard = () => {
    if (report && reviewStatus !== report.reviewStatus) {
      localStorage.setItem(
        "updatedReport",
        JSON.stringify({
          id: report.id,
          reviewStatus: reviewStatus,
        }),
      )
      window.dispatchEvent(new Event("storage"))
    }
    router.push("/gcf-dashboard")
  }

  const getRiskBadgeClass = (risk: string) => {
    switch (risk) {
      case "High":
        return "risk-high px-3 py-1 rounded-full text-sm font-medium"
      case "Medium":
        return "risk-medium px-3 py-1 rounded-full text-sm font-medium"
      case "Low":
        return "risk-low px-3 py-1 rounded-full text-sm font-medium"
      default:
        return "bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium"
    }
  }

  const highlightKeywords = (text: string, keywords: string[]) => {
    let highlightedText = text
    keywords.forEach((keyword) => {
      const regex = new RegExp(`(${keyword})`, "gi")
      highlightedText = highlightedText.replace(
        regex,
        '<mark class="bg-yellow-200 dark:bg-yellow-600/30 dark:text-yellow-200 px-1 rounded">$1</mark>',
      )
    })
    return highlightedText
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        {/* Gradient background for dark theme */}
        <div className="absolute inset-0 dark:bg-gradient-to-br dark:from-slate-900 dark:via-purple-900/20 dark:to-slate-900 pointer-events-none" />
        <div className="text-center relative z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading report...</p>
        </div>
      </div>
    )
  }

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
              {/* Theme toggle */}
              <ThemeToggle />
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
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-sm text-muted-foreground">Patient ID:</span>
                  <span className="ml-2 font-mono font-medium text-foreground">{report.patientId}</span>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Clinic:</span>
                  <span className="ml-2 font-medium text-foreground">{report.clinicName}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              <span className={getRiskBadgeClass(report.riskScore)}>{report.riskScore} Risk</span>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Original Document Viewer */}
          <Card className="h-fit card-glow dark:bg-card/80 dark:backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-foreground">
                <FileText className="w-5 h-5" />
                Original Document
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted/30 border border-border rounded-lg p-4 h-96 overflow-y-auto dark:bg-muted/10">
                <div className="bg-card p-6 rounded shadow-sm dark:bg-card/60">
                  <div className="text-center mb-4 pb-4 border-b border-border">
                    <h3 className="text-lg font-semibold text-foreground">Patient_789_Report.pdf</h3>
                    <p className="text-sm text-muted-foreground">Mammography Report</p>
                  </div>
                  <div className="space-y-4 text-sm">
                    <div className="whitespace-pre-line text-foreground leading-relaxed">{report.extractedText}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Right Panel - System Analysis */}
          <div className="space-y-6">
            {/* Risk Summary */}
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-foreground">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-muted-foreground">Calculated Risk:</span>
                    <span className={getRiskBadgeClass(report.riskScore)}>{report.riskScore}</span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-muted-foreground">Justification:</span>
                    <p className="mt-1 text-sm text-foreground">{report.riskJustification}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Extracted Text with Highlighting */}
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-foreground">Extracted Text Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-muted/30 border border-border rounded-lg p-4 h-64 overflow-y-auto dark:bg-muted/10">
                  <div
                    className="text-sm text-foreground leading-relaxed whitespace-pre-line"
                    dangerouslySetInnerHTML={{
                      __html: highlightKeywords(report.extractedText, report.highlightedKeywords),
                    }}
                  />
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="text-xs text-muted-foreground">Flagged keywords:</span>
                  {report.highlightedKeywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="bg-yellow-200 dark:bg-yellow-600/30 dark:text-yellow-200 px-2 py-1 rounded text-xs font-medium"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Action Module */}
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-foreground">Review Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-foreground mb-2 block">Update Review Status</label>
                    <Select value={reviewStatus} onValueChange={setReviewStatus}>
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
                      placeholder="Add your notes here..."
                      value={internalNotes}
                      onChange={(e) => setInternalNotes(e.target.value)}
                      rows={4}
                      className="dark:bg-muted/50 dark:border-primary/30 dark:focus:border-primary dark:focus:ring-primary/20"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <Button
                      onClick={handleSaveChanges}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground glow-secondary"
                    >
                      Save Changes
                    </Button>
                    {showSaveConfirmation && <span className="text-sm text-success font-medium">Status updated</span>}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
