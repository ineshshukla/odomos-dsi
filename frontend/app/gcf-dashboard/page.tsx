"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AuraLogo } from "@/components/aura-logo"
import { Search, AlertTriangle, Users, FileText, TrendingUp } from "lucide-react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/contexts/AuthContext"
import { listDocuments, getRiskPrediction } from "@/lib/documentApi"
import type { DocumentStatus, PredictionResult } from "@/lib/types"

interface ReportRecord {
  id: string
  documentId: string
  filename: string
  clinicName: string
  submissionDate: string
  riskScore: "High" | "Medium" | "Low" | "Pending"
  riskLevel: string
  predictedBirads: string
  confidence: number
  reviewStatus: "New" | "Under Review" | "Follow-up Initiated" | "Review Complete"
}

export default function GCFDashboardPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [riskFilter, setRiskFilter] = useState("All")
  const [clinicFilter, setClinicFilter] = useState("All")
  const [reports, setReports] = useState<ReportRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string>("")

  const router = useRouter()
  const { user, logout } = useAuth()

  // Load documents and predictions
  useEffect(() => {
    loadReports()
    
    // Auto-refresh every 10 seconds to see new predictions
    const interval = setInterval(() => {
      loadReports()
    }, 10000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const handleStorageChange = () => {
      const updatedReport = localStorage.getItem("updatedReport")
      if (updatedReport) {
        const reportData = JSON.parse(updatedReport)
        setReports((prev) =>
          prev.map((report) =>
            report.id === reportData.id ? { ...report, reviewStatus: reportData.reviewStatus } : report,
          ),
        )
        localStorage.removeItem("updatedReport")
      }
    }

    window.addEventListener("storage", handleStorageChange)
    handleStorageChange() // Check on mount

    return () => window.removeEventListener("storage", handleStorageChange)
  }, [])

  const loadReports = async () => {
    setIsLoading(true)
    setError("")
    try {
      // Fetch all documents (GCF coordinators can see all documents)
      const response = await listDocuments(1, 100)
      
      // Fetch predictions for each document
      const reportsWithPredictions = await Promise.all(
        response.documents.map(async (doc: DocumentStatus) => {
          let prediction: PredictionResult | null = null
          let riskScore: "High" | "Medium" | "Low" | "Pending" = "Pending"
          let riskLevel = "needs_assessment"
          let predictedBirads = "N/A"
          let confidence = 0
          
          try {
            // Only fetch prediction if document is structured
            if (doc.status === "structured" || doc.status === "predicted") {
              prediction = await getRiskPrediction(doc.upload_id)
              
              if (prediction) {
                riskLevel = prediction.risk_level
                predictedBirads = prediction.predicted_birads
                confidence = prediction.confidence_score
                
                // Map risk_level to riskScore
                switch (prediction.risk_level) {
                  case "high":
                    riskScore = "High"
                    break
                  case "medium":
                    riskScore = "Medium"
                    break
                  case "low":
                    riskScore = "Low"
                    break
                  default:
                    riskScore = "Pending"
                }
              }
            }
          } catch (err) {
            console.error(`Failed to load prediction for document ${doc.upload_id}:`, err)
          }
          
          return {
            id: doc.upload_id,
            documentId: doc.upload_id,
            filename: doc.file_info.filename,
            clinicName: doc.clinic_name || "Unknown Clinic",
            submissionDate: new Date(doc.upload_timestamp || doc.created_at).toLocaleDateString(),
            riskScore,
            riskLevel,
            predictedBirads,
            confidence,
            reviewStatus: (prediction?.review_status as "New" | "Under Review" | "Follow-up Initiated" | "Review Complete") || "New",
          }
        })
      )
      
      setReports(reportsWithPredictions)
    } catch (err) {
      console.error("Failed to load reports:", err)
      setError(err instanceof Error ? err.message : "Failed to load reports")
    } finally {
      setIsLoading(false)
    }
  }

  const filteredReports = reports.filter((report) => {
    const matchesSearch =
      report.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.clinicName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.documentId.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRisk = riskFilter === "All" || report.riskScore === riskFilter
    const matchesClinic = clinicFilter === "All" || report.clinicName === clinicFilter

    return matchesSearch && matchesRisk && matchesClinic
  })

  const getRiskBadgeClass = (risk: string) => {
    switch (risk) {
      case "High":
        return "risk-high px-2 py-1 rounded-full text-xs font-medium"
      case "Medium":
        return "risk-medium px-2 py-1 rounded-full text-xs font-medium"
      case "Low":
        return "risk-low px-2 py-1 rounded-full text-xs font-medium"
      case "Pending":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-1 rounded-full text-xs font-medium"
      default:
        return "bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium"
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "New":
        return "status-new px-2 py-1 rounded-full text-xs font-medium"
      case "Under Review":
        return "status-review px-2 py-1 rounded-full text-xs font-medium"
      case "Follow-up Initiated":
        return "status-followup px-2 py-1 rounded-full text-xs font-medium"
      case "Review Complete":
        return "status-complete px-2 py-1 rounded-full text-xs font-medium"
      default:
        return "bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium"
    }
  }

  const handleViewDetails = (report: ReportRecord) => {
    router.push(`/report-detail/${report.id}`)
  }

  // Calculate KPIs from real data
  const today = new Date().toLocaleDateString()
  const newReportsToday = reports.filter((r) => r.submissionDate === today).length
  const highRiskPending = reports.filter((r) => r.riskScore === "High" && r.reviewStatus !== "Review Complete").length
  const mediumRiskCases = reports.filter((r) => r.riskScore === "Medium").length
  const totalReports = reports.length

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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="space-y-8">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">New Reports Today</p>
                    <p className="text-3xl font-bold text-foreground">{newReportsToday}</p>
                  </div>
                  <FileText className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-destructive/20 card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">High-Risk Cases Pending</p>
                    <p className="text-3xl font-bold text-destructive">{highRiskPending}</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-destructive" />
                </div>
              </CardContent>
            </Card>

            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Medium-Risk Cases</p>
                    <p className="text-3xl font-bold text-warning">{mediumRiskCases}</p>
                  </div>
                  <Users className="w-8 h-8 text-warning" />
                </div>
              </CardContent>
            </Card>

            <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Total Reports Processed</p>
                    <p className="text-3xl font-bold text-foreground">{totalReports}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-success" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters and Search */}
          <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl text-foreground">Report Management</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="Search by Document or Clinic Name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 dark:bg-muted/50 dark:border-primary/30 dark:focus:border-primary dark:focus:ring-primary/20"
                  />
                </div>
                <Select value={riskFilter} onValueChange={setRiskFilter}>
                  <SelectTrigger className="w-full sm:w-48 dark:bg-muted/50 dark:border-primary/30">
                    <SelectValue placeholder="Filter by Risk" />
                  </SelectTrigger>
                  <SelectContent className="dark:bg-card dark:border-primary/30">
                    <SelectItem value="All">All Risk Levels</SelectItem>
                    <SelectItem value="High">High Risk</SelectItem>
                    <SelectItem value="Medium">Medium Risk</SelectItem>
                    <SelectItem value="Low">Low Risk</SelectItem>
                    <SelectItem value="Pending">Pending Assessment</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={clinicFilter} onValueChange={setClinicFilter}>
                  <SelectTrigger className="w-full sm:w-48 dark:bg-muted/50 dark:border-primary/30">
                    <SelectValue placeholder="Filter by Clinic" />
                  </SelectTrigger>
                  <SelectContent className="dark:bg-card dark:border-primary/30">
                    <SelectItem value="All">All Clinics</SelectItem>
                    {Array.from(new Set(reports.map(r => r.clinicName))).map(clinic => (
                      <SelectItem key={clinic} value={clinic}>{clinic}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Reports Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 font-medium text-foreground">Risk Score</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">BI-RADS</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">Document</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">Clinic Name</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">Submission Date</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">Review Status</th>
                      <th className="text-left py-3 px-4 font-medium text-foreground">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-muted-foreground">
                          Loading reports...
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-destructive">
                          {error}
                        </td>
                      </tr>
                    ) : filteredReports.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-muted-foreground">
                          No reports found
                        </td>
                      </tr>
                    ) : (
                      filteredReports.map((report) => (
                        <tr
                          key={report.id}
                          className="border-b border-border hover:bg-muted/50 dark:hover:bg-primary/5 transition-colors"
                        >
                          <td className="py-3 px-4">
                            <span className={getRiskBadgeClass(report.riskScore)}>{report.riskScore}</span>
                          </td>
                          <td className="py-3 px-4 font-mono text-foreground">
                            {report.predictedBirads}
                            {report.confidence > 0 && (
                              <span className="text-xs text-muted-foreground ml-1">
                                ({(report.confidence * 100).toFixed(1)}%)
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-foreground truncate max-w-xs" title={report.filename}>
                            {report.filename}
                          </td>
                          <td className="py-3 px-4 text-foreground">{report.clinicName}</td>
                          <td className="py-3 px-4 text-muted-foreground">{report.submissionDate}</td>
                          <td className="py-3 px-4">
                            <span className={getStatusBadgeClass(report.reviewStatus)}>{report.reviewStatus}</span>
                          </td>
                          <td className="py-3 px-4">
                            <Button
                              size="sm"
                              onClick={() => handleViewDetails(report)}
                              className="bg-primary hover:bg-primary/90 text-primary-foreground glow-primary"
                            >
                              View Details
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-muted-foreground">
                  Showing {filteredReports.length} of {reports.length} reports
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled>
                    Previous
                  </Button>
                  <Button variant="outline" size="sm" className="bg-primary text-primary-foreground glow-primary">
                    1
                  </Button>
                  <Button variant="outline" size="sm">
                    2
                  </Button>
                  <Button variant="outline" size="sm">
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
