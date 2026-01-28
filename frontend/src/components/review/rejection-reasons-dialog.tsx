'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { REJECTION_REASONS, RejectionReason } from '@/lib/rejection-reasons'

interface RejectionReasonsDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: (reasons: RejectionReason[]) => void
  isLoading?: boolean
}

export function RejectionReasonsDialog({
  open,
  onClose,
  onConfirm,
  isLoading = false,
}: RejectionReasonsDialogProps) {
  const [selected, setSelected] = useState<RejectionReason[]>([])

  const toggle = (reason: RejectionReason) => {
    setSelected((prev) =>
      prev.includes(reason)
        ? prev.filter((r) => r !== reason)
        : [...prev, reason]
    )
  }

  const handleConfirm = () => {
    onConfirm(selected)
    setSelected([]) // Reset for next use
  }

  const handleSkip = () => {
    onConfirm([]) // Reject without reasons
    setSelected([]) // Reset for next use
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setSelected([]) // Reset on close
      onClose()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Why are you rejecting this content?</DialogTitle>
          <DialogDescription>
            Select any issues to help improve regeneration (optional)
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {(Object.entries(REJECTION_REASONS) as [RejectionReason, string][]).map(
            ([key, label]) => (
              <label
                key={key}
                className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 p-2 rounded -mx-2"
              >
                <Checkbox
                  checked={selected.includes(key)}
                  onCheckedChange={() => toggle(key)}
                  disabled={isLoading}
                />
                <span className="text-sm">{label}</span>
              </label>
            )
          )}
        </div>

        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={handleSkip}
            disabled={isLoading}
            className="flex-1"
          >
            Skip
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1"
          >
            {selected.length > 0 ? 'Reject with Feedback' : 'Reject'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
