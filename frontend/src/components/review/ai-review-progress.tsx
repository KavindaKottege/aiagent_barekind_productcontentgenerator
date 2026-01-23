'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  pauseBatchAIReview,
  cancelBatchAIReview,
  resumeBatchAIReview,
  AIReviewJobStatus,
} from '@/app/actions/review'

interface AIReviewProgressProps {
  clientId: string
  accessToken: string
  onComplete?: () => void
}

interface ProgressEvent {
  status: string
  completed: number
  total: number
  cost: string
  auto_approve: boolean
  estimated_remaining: number | null
}

export function AIReviewProgress({
  clientId,
  accessToken,
  onComplete,
}: AIReviewProgressProps) {
  const [progress, setProgress] = useState<ProgressEvent | null>(null)
  const [isPausing, setIsPausing] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [isResuming, setIsResuming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // SSE connection for real-time progress
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const eventSource = new EventSource(
      `${apiUrl}/api/review/${clientId}/ai-review/progress?token=${accessToken}`
    )

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data) as ProgressEvent
      setProgress(data)
    })

    eventSource.addEventListener('complete', () => {
      eventSource.close()
      if (onComplete) {
        onComplete()
      }
    })

    eventSource.addEventListener('error', (event) => {
      // EventSource will auto-reconnect on network errors
      console.error('SSE error:', event)
    })

    return () => {
      eventSource.close()
    }
  }, [clientId, accessToken, onComplete])

  const handlePause = useCallback(async () => {
    setIsPausing(true)
    setError(null)
    const result = await pauseBatchAIReview(clientId)
    setIsPausing(false)
    if (!result.success) {
      setError('Failed to pause')
    }
  }, [clientId])

  const handleCancel = useCallback(async () => {
    setIsCancelling(true)
    setError(null)
    const result = await cancelBatchAIReview(clientId)
    setIsCancelling(false)
    if (!result.success) {
      setError('Failed to cancel')
    } else if (onComplete) {
      onComplete()
    }
  }, [clientId, onComplete])

  const handleResume = useCallback(async () => {
    setIsResuming(true)
    setError(null)
    // Resume with same auto_approve mode as when paused
    const result = await resumeBatchAIReview(clientId, progress?.auto_approve || false)
    setIsResuming(false)
    if ('error' in result) {
      setError(result.error)
    }
  }, [clientId, progress])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  if (!progress) {
    return (
      <Card className="mb-6">
        <CardContent className="py-8 text-center">
          <p className="text-gray-600">Connecting to AI review service...</p>
        </CardContent>
      </Card>
    )
  }

  const progressPercent = progress.total > 0
    ? Math.round((progress.completed / progress.total) * 100)
    : 0

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-500',
    running: 'bg-blue-500',
    paused: 'bg-orange-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
    cancelled: 'bg-gray-500',
  }

  const modeLabel = progress.auto_approve ? 'Auto-approving' : 'Recommending only'
  const modeColor = progress.auto_approve ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">AI Review Progress</CardTitle>
          <div className="flex items-center gap-2">
            <Badge className={modeColor}>
              {modeLabel}
            </Badge>
            <Badge className={statusColors[progress.status] || 'bg-gray-500'}>
              {progress.status.charAt(0).toUpperCase() + progress.status.slice(1)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>
              {progress.auto_approve ? 'Auto-reviewing' : 'Analyzing'} {progress.completed} of {progress.total} products
            </span>
            <span>{progressPercent}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Cost</p>
            <p className="font-semibold">${progress.cost}</p>
          </div>
          <div>
            <p className="text-gray-500">Estimated Remaining</p>
            <p className="font-semibold">
              {progress.estimated_remaining !== null
                ? formatTime(progress.estimated_remaining)
                : 'Calculating...'}
            </p>
          </div>
        </div>

        {/* Mode description */}
        <div className="p-3 bg-gray-50 border border-gray-200 rounded text-sm text-gray-700">
          {progress.auto_approve ? (
            <>
              <strong>AI-auto mode:</strong> Products are automatically approved or rejected based on AI recommendations. You can override any decision.
            </>
          ) : (
            <>
              <strong>AI-assisted mode:</strong> AI provides recommendations for each product. You make the final approval decision.
            </>
          )}
        </div>

        {/* Error display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Control buttons */}
        <div className="flex gap-2 pt-2">
          {progress.status === 'running' && (
            <>
              <Button
                variant="outline"
                onClick={handlePause}
                disabled={isPausing}
              >
                {isPausing ? 'Pausing...' : 'Pause'}
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={isCancelling}
              >
                {isCancelling ? 'Cancelling...' : 'Cancel'}
              </Button>
            </>
          )}
          {progress.status === 'paused' && (
            <>
              <Button
                onClick={handleResume}
                disabled={isResuming}
              >
                {isResuming ? 'Resuming...' : 'Resume'}
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={isCancelling}
              >
                {isCancelling ? 'Cancelling...' : 'Cancel'}
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
