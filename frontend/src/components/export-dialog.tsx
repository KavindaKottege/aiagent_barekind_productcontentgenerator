'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { Download, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { getExportStats, getExportToken, ExportStats } from '@/app/actions/export'

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  clientId: string
  clientName: string
}

export function ExportDialog({ open, onOpenChange, clientId, clientName }: ExportDialogProps) {
  const [stats, setStats] = useState<ExportStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [includePending, setIncludePending] = useState(false)
  const [downloading, setDownloading] = useState(false)

  // Fetch stats when dialog opens
  useEffect(() => {
    if (open) {
      setLoading(true)
      setStats(null)
      setIncludePending(false)
      getExportStats(clientId)
        .then((data) => {
          setStats(data)
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [open, clientId])

  const hasExportableContent = stats
    ? stats.approved > 0 || (includePending && stats.pending > 0)
    : false

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const token = await getExportToken()
      if (!token) {
        toast.error('Not authenticated. Please log in again.')
        return
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(
        `${API_URL}/api/export/${clientId}?include_pending=${includePending}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(err.detail || 'Export failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const today = new Date().toISOString().split('T')[0]
      a.download = `${clientName}_products_${today}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success('Export complete')
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Export failed')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Export Products</AlertDialogTitle>
          <AlertDialogDescription>
            Download product data as Excel spreadsheet for{' '}
            <span className="font-medium text-gray-900">{clientName}</span>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* Stats display */}
        <div className="space-y-3">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-10" />
                </div>
              ))}
            </div>
          ) : stats ? (
            <div className="rounded-md border border-gray-200 divide-y divide-gray-100">
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-gray-600">Total Products</span>
                <span className="text-sm font-medium text-gray-900">{stats.total}</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-green-700">Approved</span>
                <span className="text-sm font-medium text-green-700">{stats.approved}</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-gray-600">Pending Review</span>
                <span className="text-sm font-medium text-gray-900">{stats.pending}</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-red-600">Rejected</span>
                <span className="text-sm font-medium text-red-600">{stats.rejected}</span>
              </div>
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-gray-400">Not Generated</span>
                <span className="text-sm font-medium text-gray-400">{stats.not_generated}</span>
              </div>
            </div>
          ) : (
            <div className="text-sm text-red-600">Failed to load export statistics.</div>
          )}

          {/* Include pending checkbox */}
          {!loading && stats && (
            <div className="flex items-start space-x-3 pt-1">
              <Checkbox
                id="include-pending"
                checked={includePending}
                onCheckedChange={(checked) => setIncludePending(checked === true)}
              />
              <div className="grid gap-1 leading-none">
                <label
                  htmlFor="include-pending"
                  className="text-sm font-medium leading-none cursor-pointer peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Include content pending approval
                </label>
                <p className="text-xs text-gray-500">
                  Updates titles/descriptions for products awaiting review
                </p>
              </div>
            </div>
          )}

          {/* No exportable content warning */}
          {!loading && stats && !hasExportableContent && (
            <div className="flex items-start gap-3 rounded-md bg-amber-50 border border-amber-200 p-3">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">No products with updated content to export</p>
                <p className="mt-1">
                  All products will keep their original values.{' '}
                  <Link href="/review" className="underline font-medium hover:text-amber-900" onClick={() => onOpenChange(false)}>
                    Review products
                  </Link>{' '}
                  to approve generated content.
                </p>
              </div>
            </div>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={downloading}>Cancel</AlertDialogCancel>
          <Button
            onClick={handleDownload}
            disabled={downloading || loading || !stats || !hasExportableContent}
          >
            {downloading ? (
              'Downloading...'
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download
              </>
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
