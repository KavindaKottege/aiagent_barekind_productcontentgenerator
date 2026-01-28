'use client'

import { useState, useTransition, useOptimistic, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useHotkeys } from 'react-hotkeys-hook'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronLeft, ChevronRight, AlertTriangle, History } from 'lucide-react'
import {
  ProductGroupReview,
  ReviewActionResult,
  approveProduct,
  rejectProduct,
  rejectWithReasons,
  saveEditTitle,
  saveEditDescription,
  getNextUnreviewed,
  undoReview,
} from '@/app/actions/review'
import { useReviewHistory } from '@/lib/review-context'
import { RejectionReason } from '@/lib/rejection-reasons'
import { ImageDisplay } from './image-display'
import { InlineEditor } from './inline-editor'
import { AIReviewPanel } from './ai-review-panel'
import { MissingFieldsWarning } from './missing-fields-warning'
import { RejectionReasonsDialog } from './rejection-reasons-dialog'
import { GenerationHistoryDialog } from './generation-history-dialog'
import { RegenerateButton } from './regenerate-button'
import { statusBadgeStyles } from './review-stats'

interface ReviewInterfaceProps {
  product: ProductGroupReview
  clientId: string
  allProductIds: string[]
  selectedFields: string[]
  titleMinChars?: number
  titleMaxChars?: number
  descMinChars?: number
  descMaxChars?: number
}

export function ReviewInterface({
  product: initialProduct,
  clientId,
  allProductIds,
  selectedFields,
  titleMinChars = 30,
  titleMaxChars = 60,
  descMinChars = 2000,
  descMaxChars = 3000,
}: ReviewInterfaceProps) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const { recordAction, undo, redo, canUndo, canRedo } = useReviewHistory()

  // Local state
  const [currentProduct, setCurrentProduct] = useState(initialProduct)
  const [showOriginalData, setShowOriginalData] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [showHistoryDialog, setShowHistoryDialog] = useState(false)

  // Sync currentProduct when initialProduct prop changes (e.g., after router.refresh())
  useEffect(() => {
    setCurrentProduct(initialProduct)
  }, [initialProduct])

  // Optimistic state for instant UI feedback
  const [optimisticStatus, setOptimisticStatus] = useOptimistic(
    currentProduct.review_status,
    (state, newStatus: string | null) => newStatus
  )

  // Current product index for navigation
  const currentIndex = allProductIds.indexOf(currentProduct.id)
  const hasPrevious = currentIndex > 0
  const hasNext = currentIndex < allProductIds.length - 1

  // Navigation handlers
  const navigateToProduct = useCallback((productId: string) => {
    router.push(`/review/${productId}?client=${clientId}`)
  }, [router, clientId])

  const goToPrevious = useCallback(() => {
    if (hasPrevious) {
      navigateToProduct(allProductIds[currentIndex - 1])
    }
  }, [hasPrevious, allProductIds, currentIndex, navigateToProduct])

  const goToNext = useCallback(() => {
    if (hasNext) {
      navigateToProduct(allProductIds[currentIndex + 1])
    }
  }, [hasNext, allProductIds, currentIndex, navigateToProduct])

  // Approve handler
  const handleApprove = useCallback(async () => {
    setError(null)
    startTransition(async () => {
      setOptimisticStatus('approved')

      const result = await approveProduct(currentProduct.id)

      if (result.success) {
        recordAction({
          productId: currentProduct.id,
          action: 'approve',
          previousStatus: currentProduct.review_status,
        })

        // Auto-advance to next unreviewed
        if (result.next_product_id) {
          navigateToProduct(result.next_product_id)
        } else {
          // No more unreviewed, show completion message
          router.push(`/review?client=${clientId}`)
        }
      } else {
        setError(result.message || 'Failed to approve')
        setOptimisticStatus(currentProduct.review_status || null)
      }
    })
  }, [currentProduct, recordAction, navigateToProduct, clientId, router, setOptimisticStatus])

  // Reject handler - opens dialog for rejection reasons
  const handleRejectClick = useCallback(() => {
    setShowRejectDialog(true)
  }, [])

  // Confirm rejection with optional reasons
  const handleRejectConfirm = useCallback(async (reasons: RejectionReason[]) => {
    setShowRejectDialog(false)
    setError(null)
    startTransition(async () => {
      setOptimisticStatus('rejected')

      const result = await rejectWithReasons(currentProduct.id, reasons)

      if (result.success) {
        recordAction({
          productId: currentProduct.id,
          action: 'reject',
          previousStatus: currentProduct.review_status,
        })

        // Auto-advance to next unreviewed
        if (result.next_product_id) {
          navigateToProduct(result.next_product_id)
        } else {
          router.push(`/review?client=${clientId}`)
        }
      } else {
        setError(result.message || 'Failed to reject')
        setOptimisticStatus(currentProduct.review_status || null)
      }
    })
  }, [currentProduct, recordAction, navigateToProduct, clientId, router, setOptimisticStatus])

  // Undo handler - reverts database status then navigates
  const handleUndo = useCallback(async () => {
    const lastAction = undo()
    if (lastAction) {
      // Revert the database status BEFORE navigating
      const result = await undoReview(lastAction.productId, lastAction.previousStatus)
      if (result.success) {
        router.push(`/review/${lastAction.productId}?client=${clientId}`)
        router.refresh()
      } else {
        setError(result.message || 'Failed to undo')
        // Re-record the action since undo failed
        recordAction({
          productId: lastAction.productId,
          action: lastAction.action,
          previousStatus: lastAction.previousStatus,
        })
      }
    }
  }, [undo, router, clientId, recordAction])

  // Redo handler - re-applies the undone action
  const handleRedo = useCallback(async () => {
    const nextAction = redo()
    if (nextAction) {
      setError(null)
      let result: ReviewActionResult

      if (nextAction.action === 'approve') {
        result = await approveProduct(nextAction.productId)
      } else if (nextAction.action === 'reject') {
        result = await rejectProduct(nextAction.productId)
      } else {
        // Edit actions don't need redo (edits are preserved)
        router.push(`/review/${nextAction.productId}?client=${clientId}`)
        router.refresh()
        return
      }

      if (result.success) {
        router.push(`/review/${nextAction.productId}?client=${clientId}`)
        router.refresh()
      } else {
        setError(result.message || 'Failed to redo')
      }
    }
  }, [redo, router, clientId])

  // Computed display values
  const displayTitle = currentProduct.edited_title || currentProduct.generated_title || ''
  const displayDescription = currentProduct.edited_description || currentProduct.generated_description || ''

  // Save edit handlers
  const handleSaveTitle = useCallback(async (newTitle: string) => {
    const result = await saveEditTitle(currentProduct.id, newTitle)

    if (!result.success) {
      throw new Error(result.message || 'Failed to save title')
    }

    // Refresh to get updated data
    router.refresh()
    setIsEditing(false)
  }, [currentProduct, router])

  const handleSaveDescription = useCallback(async (newDescription: string) => {
    const result = await saveEditDescription(currentProduct.id, newDescription)

    if (!result.success) {
      throw new Error(result.message || 'Failed to save description')
    }

    // Refresh to get updated data
    router.refresh()
    setIsEditing(false)
  }, [currentProduct, router])

  // Regeneration handlers
  const handleRegenerateStart = useCallback((jobId: string) => {
    // Navigate to products page to see generation progress
    router.push(`/products?client=${clientId}`)
  }, [router, clientId])

  const handleHistoryRestore = useCallback(() => {
    router.refresh() // Refresh to get restored content
  }, [router])

  // Keyboard shortcuts - disabled when editing
  useHotkeys('a', () => !isEditing && handleApprove(), { enabled: !isEditing, preventDefault: true })
  useHotkeys('r', () => !isEditing && handleRejectClick(), { enabled: !isEditing, preventDefault: true })
  useHotkeys('e', () => !isEditing && setIsEditing(true), { enabled: !isEditing, preventDefault: true })
  useHotkeys('left, k', () => !isEditing && goToPrevious(), { enabled: !isEditing, preventDefault: true })
  useHotkeys('right, j', () => !isEditing && goToNext(), { enabled: !isEditing, preventDefault: true })
  useHotkeys('escape', () => setIsEditing(false), { enabled: isEditing, preventDefault: true })
  useHotkeys('ctrl+z, meta+z', () => !isEditing && handleUndo(), { enabled: canUndo && !isEditing, preventDefault: true })
  useHotkeys('ctrl+shift+z, meta+shift+z', () => !isEditing && handleRedo(), { enabled: canRedo && !isEditing, preventDefault: true })

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header with navigation */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review Product</h2>
          <p className="text-sm text-gray-600">
            Product {currentIndex + 1} of {allProductIds.length}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowHistoryDialog(true)}
          >
            <History className="w-4 h-4 mr-2" />
            History
          </Button>
          {currentProduct.review_status === 'rejected' && (
            <RegenerateButton
              productGroupId={currentProduct.id}
              onRegenerateStart={handleRegenerateStart}
            />
          )}
          <Button
            variant="outline"
            onClick={goToPrevious}
            disabled={!hasPrevious || isPending}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <Button
            variant="outline"
            onClick={goToNext}
            disabled={!hasNext || isPending}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Status indicators */}
      <div className="flex gap-2">
        {optimisticStatus && (
          <span className={`${statusBadgeStyles[optimisticStatus as keyof typeof statusBadgeStyles] || statusBadgeStyles.pending} px-3 py-1 rounded-full text-sm font-medium`}>
            {optimisticStatus === 'ai_approved' ? 'Auto-approved by AI' :
             optimisticStatus === 'ai_rejected' ? 'Auto-rejected by AI' :
             optimisticStatus === 'approved' ? 'Approved' :
             optimisticStatus === 'rejected' ? 'Rejected' :
             optimisticStatus === 'edited' ? 'Edited' :
             optimisticStatus.charAt(0).toUpperCase() + optimisticStatus.slice(1)}
          </span>
        )}
        {currentProduct.ai_review_status && !optimisticStatus?.startsWith('ai_') && (
          <Badge variant="outline">
            AI: {currentProduct.ai_review_status.replace('_', ' ')}
          </Badge>
        )}
      </div>

      {/* Safety warnings */}
      {currentProduct.ai_review_safety_flags && currentProduct.ai_review_safety_flags.length > 0 && (
        <div className="p-4 bg-orange-50 border border-orange-200 rounded flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-orange-900">AI Safety Concerns:</p>
            <ul className="list-disc list-inside text-orange-800 text-sm">
              {currentProduct.ai_review_safety_flags.map((flag, idx) => (
                <li key={idx}>{flag}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* AI review reason */}
      {currentProduct.ai_review_reason && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
          <span className="font-semibold">AI Review Note:</span> {currentProduct.ai_review_reason}
        </div>
      )}

      {/* Missing fields warning */}
      {selectedFields.length > 0 && (
        <MissingFieldsWarning product={currentProduct} selectedFields={selectedFields} />
      )}

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Generated content (60%) */}
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardContent className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Generated Title
                </label>
                <InlineEditor
                  value={displayTitle}
                  onSave={handleSaveTitle}
                  minChars={titleMinChars}
                  maxChars={titleMaxChars}
                  placeholder="Title will appear here..."
                  multiline={false}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Generated Description
                </label>
                <InlineEditor
                  value={displayDescription}
                  onSave={handleSaveDescription}
                  minChars={descMinChars}
                  maxChars={descMaxChars}
                  placeholder="Description will appear here..."
                  multiline={true}
                />
              </div>
            </CardContent>
          </Card>

          {/* Collapsible original data */}
          <Collapsible open={showOriginalData} onOpenChange={setShowOriginalData}>
            <Card>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between p-4">
                  <span className="font-semibold">Original Product Data</span>
                  <ChevronDown
                    className={`w-4 h-4 transition-transform ${showOriginalData ? 'rotate-180' : ''}`}
                  />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="px-6 pb-6 pt-0 space-y-3">
                  <div>
                    <span className="text-sm font-semibold text-gray-700">Product Name:</span>
                    <p className="text-sm text-gray-900">{currentProduct.product_name}</p>
                  </div>
                  {Object.entries(currentProduct.original_data).map(([key, value]) => {
                    if (!value) return null
                    return (
                      <div key={key}>
                        <span className="text-sm font-semibold text-gray-700 capitalize">
                          {key.replace(/_/g, ' ')}:
                        </span>
                        <p className="text-sm text-gray-900">{String(value)}</p>
                      </div>
                    )
                  })}
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        </div>

        {/* Right: Images and AI Review (40%) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardContent className="p-4">
              <ImageDisplay images={currentProduct.images} />
            </CardContent>
          </Card>

          {/* AI Review Panel */}
          <AIReviewPanel
            product={currentProduct}
            onAIReviewComplete={() => router.refresh()}
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-between border-t pt-6">
        <div className="space-y-1">
          <div className="flex gap-4 text-sm text-gray-600">
            <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">A</kbd> Approve</span>
            <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">R</kbd> Reject</span>
            <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">E</kbd> Edit</span>
            <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">←/→</kbd> Navigate</span>
          </div>
          {(canUndo || canRedo) && (
            <div className="text-sm text-gray-600 flex gap-4">
              {canUndo && (
                <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">Ctrl+Z</kbd> Undo</span>
              )}
              {canRedo && (
                <span><kbd className="px-2 py-1 bg-gray-100 rounded border text-xs">Ctrl+Shift+Z</kbd> Redo</span>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleRejectClick}
            disabled={isPending}
            className="min-w-[120px] border-red-300 text-red-700 hover:bg-red-50 hover:text-red-800"
          >
            Reject (R)
          </Button>
          <Button
            onClick={handleApprove}
            disabled={isPending}
            className="min-w-[120px] bg-brand-green hover:bg-brand-green-hover text-white"
          >
            Approve (A)
          </Button>
        </div>
      </div>

      {/* Rejection reasons dialog */}
      <RejectionReasonsDialog
        open={showRejectDialog}
        onClose={() => setShowRejectDialog(false)}
        onConfirm={handleRejectConfirm}
        isLoading={isPending}
      />

      {/* Generation history dialog */}
      <GenerationHistoryDialog
        productGroupId={currentProduct.id}
        open={showHistoryDialog}
        onClose={() => setShowHistoryDialog(false)}
        onRestore={handleHistoryRestore}
      />
    </div>
  )
}
