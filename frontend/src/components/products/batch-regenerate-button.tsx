'use client'

import { useState, useEffect, useTransition } from 'react'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { RefreshCw, Loader2 } from 'lucide-react'
import {
  getRegenerationEstimate,
  regenerateRejected,
  RegenerationEstimate,
} from '@/app/actions/regeneration'

interface BatchRegenerateButtonProps {
  clientId: string
  rejectedCount?: number // Optional: pass pre-computed count to skip estimate fetch
  onRegenerateStart?: (jobId: string) => void
}

export function BatchRegenerateButton({
  clientId,
  rejectedCount: initialCount,
  onRegenerateStart,
}: BatchRegenerateButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [estimate, setEstimate] = useState<RegenerationEstimate | null>(null)
  const [isLoadingEstimate, setIsLoadingEstimate] = useState(false)
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  // Fetch estimate when dialog opens
  useEffect(() => {
    if (showConfirm && !estimate) {
      setIsLoadingEstimate(true)
      getRegenerationEstimate(clientId).then((data) => {
        setEstimate(data)
        setIsLoadingEstimate(false)
      })
    }
  }, [showConfirm, clientId, estimate])

  const handleRegenerate = () => {
    startTransition(async () => {
      setError(null)
      const result = await regenerateRejected(clientId)

      if ('error' in result) {
        setError(result.error)
        return
      }

      if (onRegenerateStart) {
        onRegenerateStart(result.job_id)
      }
      setShowConfirm(false)
    })
  }

  // Use passed count or estimate count
  const displayCount = estimate?.rejected_count ?? initialCount ?? 0

  // Don't show button if no rejected products
  if (initialCount !== undefined && initialCount === 0) {
    return null
  }

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setShowConfirm(true)}
        disabled={isPending}
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        Regenerate Rejected
      </Button>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Regenerate All Rejected Products?</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div>
                {isLoadingEstimate ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading estimate...
                  </span>
                ) : estimate && estimate.rejected_count > 0 ? (
                  <span>
                    This will regenerate{' '}
                    <strong>{estimate.rejected_count} rejected product{estimate.rejected_count !== 1 ? 's' : ''}</strong>{' '}
                    using rejection feedback to create improved content.
                    <br />
                    <br />
                    <span className="text-gray-600">
                      Estimated cost: <strong>{estimate.estimated_cost}</strong>
                    </span>
                    <br />
                    <span className="text-gray-600 text-sm">
                      Previous versions will be preserved in history.
                    </span>
                  </span>
                ) : (
                  <span>No rejected products to regenerate.</span>
                )}
                {error && (
                  <span className="block mt-3 text-red-600">{error}</span>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRegenerate}
              disabled={isPending || isLoadingEstimate || !estimate || estimate.rejected_count === 0}
            >
              {isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Starting...
                </span>
              ) : (
                `Regenerate ${displayCount} Product${displayCount !== 1 ? 's' : ''}`
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
