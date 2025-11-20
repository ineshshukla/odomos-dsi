"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AuraLogo } from "@/components/aura-logo"
import { Upload, FileText, CheckCircle, Clock, AlertCircle, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/contexts/AuthContext"
import { uploadDocument, uploadZipFile, listDocuments, deleteDocument } from "@/lib/documentApi"
import type { DocumentStatus } from "@/lib/types"

export default function ClinicPortalPage() {
  const router = useRouter()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [showSuccess, setShowSuccess] = useState(false)
  const [uploadedCount, setUploadedCount] = useState(0)
  const [documents, setDocuments] = useState<DocumentStatus[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string>("")
  const [currentPage, setCurrentPage] = useState(1)
  const [totalDocuments, setTotalDocuments] = useState(0)
  const { user, logout } = useAuth()

  // Load documents on mount
  useEffect(() => {
    loadDocuments()
    
    // Auto-refresh every 5 seconds to see status updates
    const interval = setInterval(() => {
      loadDocuments()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [currentPage])

  const loadDocuments = async () => {
    setIsLoading(true)
    setError("")
    try {
      const response = await listDocuments(currentPage, 10)
      setDocuments(response.documents)
      setTotalDocuments(response.total)
    } catch (err) {
      console.error("Failed to load documents:", err)
      setError(err instanceof Error ? err.message : "Failed to load documents")
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setUploadProgress(0)
    setShowSuccess(false)
    setError("")
    setUploadedCount(0)

    try {
      // Check if file is a zip
      const isZip = file.name.toLowerCase().endsWith('.zip')
      
      // Start progress animation
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + (isZip ? 5 : 10), 90))
      }, isZip ? 200 : 100)

      // Upload file (backend automatically handles ZIP extraction)
      const response = await uploadDocument(file)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      
      // Handle response - could be single object or array for ZIP files
      if (Array.isArray(response)) {
        // ZIP file response - array of documents
        setUploadedCount(response.length)
        console.log(`✅ Uploaded ${response.length} documents from ZIP file`)
      } else {
        // Single file response
        setUploadedCount(1)
        console.log(`✅ Uploaded document: ${response.file_info.filename}`)
      }
      
      setIsUploading(false)
      setShowSuccess(true)

      // Reload documents list
      await loadDocuments()

      // Hide success message after appropriate time
      setTimeout(() => setShowSuccess(false), isZip ? 5000 : 3000)
    } catch (err) {
      console.error("Upload failed:", err)
      setError(err instanceof Error ? err.message : "Upload failed")
      setIsUploading(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this document?")) {
      return
    }

    try {
      await deleteDocument(documentId)
      // Reload documents list
      await loadDocuments()
    } catch (err) {
      console.error("Delete failed:", err)
      setError(err instanceof Error ? err.message : "Failed to delete document")
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0 && files[0]) {
      handleFileUpload(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0 && files[0]) {
      handleFileUpload(files[0])
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return <Clock className="w-4 h-4 text-yellow-500" />
      case "uploaded":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "parsed":
        return <CheckCircle className="w-4 h-4 text-blue-500" />
      case "structured":
        return <CheckCircle className="w-4 h-4 text-purple-500" />
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case "processing":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
      case "uploaded":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      case "parsed":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
      case "structured":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
      case "predicted":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
    }
  }

  const getStatusMessage = (status: string) => {
    switch (status) {
      case "uploaded":
        return "📄 Document uploaded - Parsing text from PDF... This may take 1-2 minutes."
      case "parsed":
        return "✅ Text extracted - Analyzing medical content and structuring data..."
      case "structured":
        return "🔬 Data structured - Running AI risk prediction model..."
      case "predicted":
        return "✅ Analysis complete! Click to view detailed results and BI-RADS classification."
      case "failed":
        return "❌ Processing failed - Please check the document format and try uploading again."
      case "processing":
        return "⏳ Processing document - Please wait while we analyze your report..."
      default:
        return status
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
    return (bytes / (1024 * 1024)).toFixed(2) + " MB"
  }

  return (
    <ProtectedRoute allowedRoles={['clinic_admin']}>
    <div className="min-h-screen bg-background"
>
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
                <p className="text-sm font-medium text-foreground">{user?.full_name || "Admin"}</p>
                <p className="text-xs text-muted-foreground">{user?.organization || "City Imaging Center"}</p>
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
          {/* Upload Section */}
          <Card className="border-2 border-dashed border-border hover:border-primary/50 transition-colors card-glow upload-glow dark:bg-card/80 dark:backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl text-center text-foreground">Upload Mammogram Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {error && !isUploading && !showSuccess && (
                <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 rounded-md flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              )}
              <div className="relative p-8 text-center" onDragOver={handleDragOver} onDrop={handleDrop}>
                {isUploading ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center glow-primary">
                      <Upload className="w-8 h-8 text-primary animate-pulse" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-foreground font-medium">Uploading...</p>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all duration-300 glow-primary"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-sm text-muted-foreground">{uploadProgress}% complete</p>
                    </div>
                  </div>
                ) : showSuccess ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 mx-auto bg-success/10 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-8 h-8 text-success" />
                    </div>
                    <p className="text-success font-medium text-lg">
                      {uploadedCount > 1 
                        ? `Successfully uploaded ${uploadedCount} documents!` 
                        : "Upload successful!"}
                    </p>
                    {uploadedCount > 1 && (
                      <p className="text-sm text-muted-foreground">
                        All documents are now being processed in parallel
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center glow-primary">
                      <Upload className="w-8 h-8 text-primary" />
                    </div>
                    <div>
                      <p className="text-lg font-medium text-foreground mb-2">Drag & Drop Report Files Here</p>
                      <p className="text-muted-foreground mb-4">Supported formats: PDF, ZIP (for multiple PDFs)</p>
                      <div className="relative">
                        <input
                          type="file"
                          accept=".pdf,.dcm,.zip"
                          onChange={handleFileSelect}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <Button
                          variant="outline"
                          className="border-primary text-primary hover:bg-primary hover:text-primary-foreground bg-transparent glow-secondary"
                        >
                          Or Browse Files
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        💡 Upload a ZIP file to process multiple reports at once
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Submission History */}
          <Card className="card-glow dark:bg-card/80 dark:backdrop-blur-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl text-foreground">Submission History</CardTitle>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3 animate-pulse" />
                  <span>Auto-refreshing every 5s</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 rounded-md">
                  {error}
                </div>
              )}
              {isLoading ? (
                <div className="text-center py-8">
                  <Clock className="w-8 h-8 text-primary animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">Loading documents...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">No documents uploaded yet</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-3 px-4 font-medium text-foreground">File Name</th>
                          <th className="text-left py-3 px-4 font-medium text-foreground">Size</th>
                          <th className="text-left py-3 px-4 font-medium text-foreground">Upload Date & Time</th>
                          <th className="text-left py-3 px-4 font-medium text-foreground">Status</th>
                          <th className="text-left py-3 px-4 font-medium text-foreground">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {documents.map((doc) => (
                          <tr
                            key={doc.upload_id}
                            className="border-b border-border hover:bg-muted/50 dark:hover:bg-primary/5 transition-colors"
                          >
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <FileText className="w-4 h-4 text-muted-foreground" />
                                <span className="text-foreground">{doc.file_info.filename}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-muted-foreground">
                              {formatFileSize(doc.file_info.size)}
                            </td>
                            <td className="py-3 px-4 text-muted-foreground">{formatDate(doc.created_at)}</td>
                            <td className="py-3 px-4">
                              <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                  {getStatusIcon(doc.status)}
                                  <span
                                    className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClass(doc.status)}`}
                                  >
                                    {doc.status.toUpperCase()}
                                  </span>
                                </div>
                                {/* Show progress bar for uploaded/processing status */}
                                {(doc.status === "uploaded" || doc.status === "processing") && (
                                  <div className="w-full bg-muted rounded-full h-1.5">
                                    <div
                                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-300 animate-pulse"
                                      style={{ width: "60%" }}
                                    />
                                  </div>
                                )}
                                <span className="text-xs text-muted-foreground font-medium">
                                  {getStatusMessage(doc.status)}
                                </span>
                                {doc.status === "failed" && doc.error && (
                                  <span className="text-xs text-red-600 dark:text-red-400 font-medium bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
                                    ⚠️ Error: {doc.error}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(doc.upload_id)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-100 dark:hover:bg-red-900/30"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Showing {documents.length} of {totalDocuments} documents
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => p + 1)}
                        disabled={documents.length < 10}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
