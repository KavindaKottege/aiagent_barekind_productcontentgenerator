'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  pauseGeneration,
  cancelGeneration,
  resumeGeneration,
  GenerationJob,
  GenerationProgress as ProgressData,
  SoftCapInfo,
} from '@/app/actions/generation'
import { SoftCapDialog } from './soft-cap-dialog'

interface GenerationProgressProps {
  jobId: string
  initialJob: GenerationJob
  onComplete: () => void
  accessToken: string
}

export function GenerationProgress({
  jobId,
  initialJob,
  onComplete,
  accessToken,
}: GenerationProgressProps) {
  const [progress, setProgress] = useState<ProgressData>({
    status: initialJob.status,
    completed: initialJob.completed_count,
    total: initialJob.total_count,
    success: initialJob.success_count,
    failed: initialJob.failed_count,
    cost: initialJob.total_cost,
    projected_cost: initialJob.total_cost,
    elapsed_seconds: 0,
    estimated_remaining_seconds: null,
  })
  const [softCapInfo, setSoftCapInfo] = useState<SoftCapInfo | null>(null)
  const [isPausing, setIsPausing] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [isResuming, setIsResuming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // SSE connection for real-time progress
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const eventSource = new EventSource(
      `${apiUrl}/api/generation/jobs/${jobId}/progress?token=${accessToken}`
    )

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data) as ProgressData
      setProgress(data)
    })

    eventSource.addEventListener('soft_cap', (event) => {
      const data = JSON.parse(event.data) as SoftCapInfo
      setSoftCapInfo(data)
    })

    eventSource.addEventListener('complete', (event) => {
      eventSource.close()
      onComplete()
    })

    eventSource.addEventListener('error', (event) => {
      // EventSource will auto-reconnect on network errors
      // Only close on explicit error events from server
      if (event.type === 'error') {
        console.error('SSE error:', event)
      }
    })

    return () => {
      eventSource.close()
    }
  }, [jobId, onComplete, accessToken])

  const handlePause = useCallback(async () => {
    setIsPausing(true)
    setError(null)
    const result = await pauseGeneration(jobId)
    setIsPausing(false)
    if (!result.success) {
      setError(result.error || 'Failed to pause')
    }
  }, [jobId])

  const handleCancel = useCallback(async () => {
    setIsCancelling(true)
    setError(null)
    const result = await cancelGeneration(jobId)
    setIsCancelling(false)
    if (!result.success) {
      setError(result.error || 'Failed to cancel')
    } else {
      onComplete()
    }
  }, [jobId, onComplete])

  const handleResume = useCallback(async () => {
    setIsResuming(true)
    setError(null)
    const result = await resumeGeneration(jobId)
    setIsResuming(false)
    if (!result.success) {
      setError(result.error || 'Failed to resume')
    }
  }, [jobId])

  const handleSoftCapResponse = useCallback(async (continueGeneration: boolean) => {
    setSoftCapInfo(null)
    if (continueGeneration) {
      // Resume will be handled by the dialog
      await handleResume()
    }
    // If not continuing, job stays paused
  }, [handleResume])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
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

  return (
    <>
      <Card className="mb-6">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Generation Progress</CardTitle>
            <Badge className={statusColors[progress.status] || 'bg-gray-500'}>
              {progress.status.charAt(0).toUpperCase() + progress.status.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>{progress.completed} / {progress.total} products</span>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Successful</p>
              <p className="font-semibold text-green-600">{progress.success}</p>
            </div>
            <div>
              <p className="text-gray-500">Failed</p>
              <p className="font-semibold text-red-600">{progress.failed}</p>
            </div>
            <div>
              <p className="text-gray-500">Cost</p>
              <p className="font-semibold">${progress.cost} (est. ${progress.projected_cost})</p>
            </div>
            <div>
              <p className="text-gray-500">Time</p>
              <p className="font-semibold">
                {formatTime(progress.elapsed_seconds)}
                {progress.estimated_remaining_seconds !== null && (
                  <span className="text-gray-500 font-normal">
                    {' '}(~{formatTime(progress.estimated_remaining_seconds)} left)
                  </span>
                )}
              </p>
            </div>
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
            {progress.status === 'paused' && !softCapInfo && (
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

      {/* Soft cap dialog */}
      {softCapInfo && (
        <SoftCapDialog
          info={softCapInfo}
          jobId={jobId}
          onResponse={handleSoftCapResponse}
        />
      )}
    </>
  )
}
