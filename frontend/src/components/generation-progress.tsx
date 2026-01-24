'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  pauseGeneration,
  cancelGeneration,
  resumeGeneration,
  forceCancelJob,
  resetJob,
  deleteJob,
  GenerationJob,
  GenerationProgress as ProgressData,
  SoftCapInfo,
} from '@/app/actions/generation'
import { SoftCapDialog } from './soft-cap-dialog'

interface GenerationProgressProps {
  jobId: string
  initialJob: GenerationJob
  onComplete: () => void
}

export function GenerationProgress({
  jobId,
  initialJob,
  onComplete,
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
    input_cost: initialJob.total_input_cost || '0',
    cached_input_cost: initialJob.total_cached_input_cost || '0',
    output_cost: initialJob.total_output_cost || '0',
    input_tokens: initialJob.total_input_tokens || 0,
    cached_input_tokens: initialJob.total_cached_input_tokens || 0,
    output_tokens: initialJob.total_output_tokens || 0,
  })
  const [softCapInfo, setSoftCapInfo] = useState<SoftCapInfo | null>(null)
  // Local display time that updates every second while running
  const [displayElapsed, setDisplayElapsed] = useState(initialJob.elapsed_seconds || 0)
  const [isPausing, setIsPausing] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [isForceCancelling, setIsForceCancelling] = useState(false)
  const [isResuming, setIsResuming] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Poll for job progress (more reliable than SSE)
  useEffect(() => {
    let isActive = true
    let pollInterval: NodeJS.Timeout | null = null

    const pollProgress = async () => {
      try {
        const result = await import('@/app/actions/generation').then(m => m.getJobStatus(jobId))

        if (!isActive) return

        if (result.success && result.job) {
          const job = result.job

          // Use elapsed_seconds from job (cumulative running time, excludes paused time)
          const elapsedSeconds = job.elapsed_seconds || 0

          // Estimate remaining time
          let estimatedRemaining: number | null = null
          if (job.completed_count > 0 && job.total_count > job.completed_count) {
            const avgTime = elapsedSeconds / job.completed_count
            estimatedRemaining = Math.floor(avgTime * (job.total_count - job.completed_count))
          }

          // Project total cost based on current rate
          let projectedCost = job.total_cost
          if (job.completed_count > 0 && job.total_count > 0) {
            const costPerProduct = parseFloat(job.total_cost) / job.completed_count
            projectedCost = (costPerProduct * job.total_count).toFixed(4)
          }

          setProgress({
            status: job.status,
            completed: job.completed_count,
            total: job.total_count,
            success: job.success_count,
            failed: job.failed_count,
            cost: job.total_cost,
            projected_cost: projectedCost,
            elapsed_seconds: elapsedSeconds,
            estimated_remaining_seconds: estimatedRemaining,
            input_cost: job.total_input_cost || '0',
            cached_input_cost: job.total_cached_input_cost || '0',
            output_cost: job.total_output_cost || '0',
            input_tokens: job.total_input_tokens || 0,
            cached_input_tokens: job.total_cached_input_tokens || 0,
            output_tokens: job.total_output_tokens || 0,
          })

          // Check for soft cap pause - show dialog
          console.log('[Poll] Job status:', job.status, 'status_reason:', job.status_reason)
          if (job.status === 'paused' && job.status_reason?.startsWith('Cost soft cap')) {
            console.log('[Poll] Soft cap detected, showing dialog')
            setSoftCapInfo({
              current_cost: job.total_cost,
              projected_cost: projectedCost,
              soft_cap: job.status_reason.match(/\$[\d.]+/)?.[0]?.replace('$', '') || '0',
              completed: job.completed_count,
              total: job.total_count,
              message: job.status_reason,
            })
          }

          // Check for terminal states
          if (['completed', 'failed', 'cancelled'].includes(job.status)) {
            if (pollInterval) clearInterval(pollInterval)
            onComplete()
          }
        }
      } catch (error) {
        console.error('[Poll] Error fetching job status:', error)
      }
    }

    // Initial poll
    pollProgress()

    // Poll every 1 second
    pollInterval = setInterval(pollProgress, 1000)

    return () => {
      isActive = false
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [jobId, onComplete])

  // Increment display elapsed every second while running
  useEffect(() => {
    if (progress.status !== 'running') return

    const timer = setInterval(() => {
      setDisplayElapsed(prev => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [progress.status])

  // Sync display elapsed when backend updates come in
  useEffect(() => {
    setDisplayElapsed(progress.elapsed_seconds)
  }, [progress.elapsed_seconds])

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

  const handleForceCancel = useCallback(async () => {
    setIsForceCancelling(true)
    setError(null)
    const result = await forceCancelJob(jobId)
    setIsForceCancelling(false)
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
    } else {
      // Resume creates a NEW job - trigger refresh to track the new job
      onComplete()
    }
  }, [jobId, onComplete])

  const handleReset = useCallback(async () => {
    setIsResetting(true)
    setError(null)
    const result = await resetJob(jobId)
    setIsResetting(false)
    if (!result.success) {
      setError(result.error || 'Failed to reset')
    } else {
      onComplete()
    }
  }, [jobId, onComplete])

  const handleDelete = useCallback(async () => {
    setIsDeleting(true)
    setError(null)
    const result = await deleteJob(jobId)
    setIsDeleting(false)
    if (!result.success) {
      setError(result.error || 'Failed to delete')
    } else {
      onComplete()
    }
  }, [jobId, onComplete])

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
              <div className="flex items-center gap-3">
                <div>
                  <p className="font-bold text-xl">${progress.cost}</p>
                  <p className="text-xs text-gray-400">est. ${progress.projected_cost}</p>
                </div>
                <div className="text-xs text-gray-500 border-l pl-2 font-mono tabular-nums">
                  <p className="flex justify-between gap-1"><span>Input</span><span>${parseFloat(progress.input_cost || '0').toFixed(4)}</span></p>
                  <p className="flex justify-between gap-1"><span>Cached</span><span>${parseFloat(progress.cached_input_cost || '0').toFixed(4)}</span></p>
                  <p className="flex justify-between gap-1"><span>Output</span><span>${parseFloat(progress.output_cost || '0').toFixed(4)}</span></p>
                </div>
              </div>
            </div>
            <div>
              <p className="text-gray-500">Time</p>
              <p className="font-semibold">
                {formatTime(displayElapsed)}
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
            {(progress.status === 'pending' || progress.status === 'running') && (
              <>
                {progress.status === 'running' && (
                  <Button
                    variant="outline"
                    onClick={handlePause}
                    disabled={isPausing}
                  >
                    {isPausing ? 'Pausing...' : 'Pause'}
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isCancelling}
                >
                  {isCancelling ? 'Cancelling...' : 'Cancel'}
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleForceCancel}
                  disabled={isForceCancelling}
                >
                  {isForceCancelling ? 'Clearing...' : 'Cancel & Clear'}
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
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isCancelling}
                >
                  {isCancelling ? 'Cancelling...' : 'Cancel'}
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleForceCancel}
                  disabled={isForceCancelling}
                >
                  {isForceCancelling ? 'Clearing...' : 'Cancel & Clear'}
                </Button>
              </>
            )}
            {['completed', 'failed', 'cancelled'].includes(progress.status) && (
              <>
                <Button
                  variant="outline"
                  onClick={handleReset}
                  disabled={isResetting}
                >
                  {isResetting ? 'Resetting...' : 'Reset & Retry'}
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete Job'}
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
