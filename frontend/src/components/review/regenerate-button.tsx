'use client'

import { useState, useTransition } from 'react'
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
import { RefreshCw } from 'lucide-react'
import { regenerateSingle } from '@/app/actions/regeneration'

interface RegenerateButtonProps {
  productGroupId: string
  onRegenerateStart: (jobId: string) => void
}

export function RegenerateButton({
  productGroupId,
  onRegenerateStart,
}: RegenerateButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  const handleRegenerate = () => {
    startTransition(async () => {
      setError(null)
      const result = await regenerateSingle(productGroupId)

      if ('error' in result) {
        setError(result.error)
        return
      }

      onRegenerateStart(result.job_id)
      setShowConfirm(false)
    })
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowConfirm(true)}
        disabled={isPending}
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        Regenerate
      </Button>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Regenerate Content?</AlertDialogTitle>
            <AlertDialogDescription>
              This will regenerate the title and description using the rejection
              feedback to create improved content. The current content will be
              preserved in history.
              {error && (
                <span className="block mt-2 text-red-600">{error}</span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRegenerate} disabled={isPending}>
              {isPending ? 'Starting...' : 'Regenerate'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
