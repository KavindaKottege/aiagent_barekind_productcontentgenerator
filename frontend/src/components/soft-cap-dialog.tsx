'use client'

import { useState } from 'react'
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
import { softCapContinue, SoftCapInfo } from '@/app/actions/generation'

interface SoftCapDialogProps {
  info: SoftCapInfo
  jobId: string
  onResponse: (continueGeneration: boolean) => void
}

export function SoftCapDialog({ info, jobId, onResponse }: SoftCapDialogProps) {
  const [isProcessing, setIsProcessing] = useState(false)

  const handleContinue = async () => {
    setIsProcessing(true)
    await softCapContinue(jobId, true)
    onResponse(true)
    setIsProcessing(false)
  }

  const handleStop = async () => {
    setIsProcessing(true)
    await softCapContinue(jobId, false)
    onResponse(false)
    setIsProcessing(false)
  }

  return (
    <AlertDialog open={true}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Cost Limit Reached</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p>
                Generation has been paused because the cost soft cap has been reached.
              </p>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Current cost:</span>
                  <span className="font-semibold">${info.current_cost}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Projected total:</span>
                  <span className="font-semibold">${info.projected_cost}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Soft cap:</span>
                  <span className="font-semibold">${info.soft_cap}</span>
                </div>
                <div className="flex justify-between border-t pt-2 mt-2">
                  <span className="text-gray-600">Progress:</span>
                  <span className="font-semibold">{info.completed} / {info.total} products</span>
                </div>
              </div>

              <p className="text-sm text-gray-600">
                Do you want to continue generating content for the remaining{' '}
                {info.total - info.completed} products?
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleStop} disabled={isProcessing}>
            {isProcessing ? 'Processing...' : 'Stop Generation'}
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleContinue} disabled={isProcessing}>
            {isProcessing ? 'Processing...' : 'Continue Generation'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
