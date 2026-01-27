'use client'

import { useState, useRef, useTransition, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { uploadProducts, UploadResult } from '@/app/actions/products'

interface UploadModalProps {
  selectedClientId: string | null
  selectedClientName: string | null
  hasExistingProducts?: boolean
}

export function UploadModal({ selectedClientId, selectedClientName, hasExistingProducts = false }: UploadModalProps) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isPending, startTransition] = useTransition()
  const [result, setResult] = useState<UploadResult | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setFile(null)
      setResult(null)
      setDragOver(false)
    }
  }, [open])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setResult(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
      setFile(droppedFile)
      setResult(null)
    }
  }

  const handleUpload = () => {
    if (!file || !selectedClientId) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('clientId', selectedClientId)

    startTransition(async () => {
      const uploadResult = await uploadProducts(formData)
      setResult(uploadResult)

      if (uploadResult.success) {
        // Wait briefly to show success, then redirect
        setTimeout(() => {
          setOpen(false)
          router.push('/products')
          router.refresh()
        }, 1500)
      }
    })
  }

  const canUpload = file && selectedClientId && !isPending

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default" size="sm">
          Upload Products
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Products</DialogTitle>
          <DialogDescription>
            Upload a Faire Excel file to import products for{' '}
            {selectedClientName ? (
              <span className="font-medium">{selectedClientName}</span>
            ) : (
              'your selected client'
            )}
            .
          </DialogDescription>
        </DialogHeader>

        {!selectedClientId && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-sm text-yellow-800">
            Please select a client from the dropdown before uploading.
          </div>
        )}

        {selectedClientId && hasExistingProducts && !result?.success && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-4 text-sm text-amber-800">
            <strong>Warning:</strong> Uploading a new file will replace all existing products for this client.
            Any generated content and review status will be lost.
          </div>
        )}

        {selectedClientId && !result?.success && (
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <div className="space-y-2">
                <div className="text-lg font-medium text-gray-900">{file.name}</div>
                <div className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Choose Different File
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-gray-600">
                  Drag and drop your Excel file here, or
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Browse Files
                </Button>
                <div className="text-xs text-gray-500 mt-2">
                  Supports .xlsx and .xls files up to 10MB
                </div>
              </div>
            )}
          </div>
        )}

        {result && !result.success && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-800">
            {result.error}
          </div>
        )}

        {result?.success && result.data && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 space-y-3">
            <div className="text-green-800 font-medium">Upload successful!</div>
            <div className="text-sm text-green-700 space-y-1">
              <div>Total rows: {result.data.total_rows}</div>
              <div>Unique Products: {result.data.product_groups}</div>
              {result.data.variant_groups > 0 && (
                <div>Products with Variants: {result.data.variant_groups}</div>
              )}
            </div>
            <div className="text-sm text-green-600">
              Redirecting to products page...
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!canUpload}
          >
            {isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
