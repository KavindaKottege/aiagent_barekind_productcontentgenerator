'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Sparkles, CheckCircle2, XCircle, Loader2, Pause, X, Play, Clock, DollarSign, Timer } from 'lucide-react'
import {
  pauseBatchAIReview,
  cancelBatchAIReview,
  resumeBatchAIReview,
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
  elapsed_seconds: number
  estimated_remaining_seconds: number | null
  approved_count: number
  rejected_count: number
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
    const sseUrl = `${apiUrl}/api/review/${clientId}/ai-review/progress?token=${accessToken}`
    console.log('[SSE] Connecting to:', sseUrl)

    const eventSource = new EventSource(sseUrl)

    eventSource.onopen = () => {
      console.log('[SSE] Connection opened')
    }

    eventSource.addEventListener('progress', (event) => {
      console.log('[SSE] Progress event received:', event.data)
      const data = JSON.parse(event.data) as ProgressEvent
      setProgress(data)
    })

    eventSource.addEventListener('complete', () => {
      console.log('[SSE] Complete event received')
      eventSource.close()
      if (onComplete) {
        onComplete()
      }
    })

    eventSource.addEventListener('error', (event) => {
      console.error('[SSE] Error:', event, 'readyState:', eventSource.readyState)
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
    const result = await resumeBatchAIReview(clientId, false)
    setIsResuming(false)
    if ('error' in result) {
      setError(result.error)
    }
  }, [clientId])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins === 0) return `${secs}s`
    return `${mins}m ${secs}s`
  }

  // Loading state with animation
  if (!progress) {
    return (
      <Card className="mb-4 border border-brand-blue/30 bg-gradient-to-r from-brand-blue/5 to-purple-50/50">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-full bg-brand-blue/10 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-brand-blue animate-pulse" />
              </div>
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-brand-blue/30 border-t-brand-blue animate-spin" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Starting AI Review</p>
              <p className="text-sm text-gray-500">Connecting to AI service...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const progressPercent = progress.total > 0
    ? Math.round((progress.completed / progress.total) * 100)
    : 0

  const isRunning = progress.status === 'running'
  const isPaused = progress.status === 'paused'

  return (
    <Card className="mb-4 border border-brand-blue/30 overflow-hidden">
      {/* Animated header bar */}
      <div className="h-1 bg-gray-200 relative overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-blue to-purple-500 transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
        {isRunning && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
        )}
      </div>

      <CardContent className="py-4 px-4">
        <div className="flex items-center gap-4">
          {/* Compact circular progress */}
          <div className="relative flex-shrink-0">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="26"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="6"
              />
              <circle
                cx="32"
                cy="32"
                r="26"
                fill="none"
                stroke="url(#progressGradient)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={`${progressPercent * 1.63} 163`}
                className="transition-all duration-500 ease-out"
              />
              <defs>
                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#2563eb" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              {isRunning ? (
                <Loader2 className="w-4 h-4 text-brand-blue animate-spin" />
              ) : isPaused ? (
                <Pause className="w-4 h-4 text-orange-500" />
              ) : (
                <Sparkles className="w-4 h-4 text-brand-blue" />
              )}
              <span className="text-sm font-bold text-gray-900 mt-0.5">{progressPercent}%</span>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Top row: progress count + status badge */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold text-gray-900">{progress.completed}</span>
                <span className="text-gray-500">/ {progress.total} reviewed</span>
              </div>
              <Badge
                className={`${
                  isRunning ? 'bg-brand-blue' : isPaused ? 'bg-orange-500' : 'bg-gray-500'
                } text-white text-xs px-2 py-0.5`}
              >
                {progress.status.charAt(0).toUpperCase() + progress.status.slice(1)}
              </Badge>
            </div>

            {/* Middle row: Approved/Rejected + Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="font-semibold">{progress.approved_count}</span>
                </span>
                <span className="flex items-center gap-1 text-red-600">
                  <XCircle className="w-4 h-4" />
                  <span className="font-semibold">{progress.rejected_count}</span>
                </span>
              </div>
              <span className="text-gray-300">|</span>
              <div className="flex items-center gap-3 text-gray-600">
                <span className="flex items-center gap-1">
                  <DollarSign className="w-3.5 h-3.5" />
                  <span>{progress.cost}</span>
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{formatTime(progress.elapsed_seconds)}</span>
                </span>
                <span className="flex items-center gap-1">
                  <Timer className="w-3.5 h-3.5" />
                  <span>
                    {progress.estimated_remaining_seconds !== null
                      ? formatTime(progress.estimated_remaining_seconds)
                      : '...'}
                  </span>
                </span>
              </div>
            </div>

            {/* Error display */}
            {error && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
                {error}
              </div>
            )}

            {/* Control buttons */}
            <div className="flex gap-2 mt-3">
              {isRunning && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePause}
                    disabled={isPausing}
                    className="h-8"
                  >
                    <Pause className="w-3.5 h-3.5 mr-1.5" />
                    {isPausing ? 'Pausing...' : 'Pause'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    disabled={isCancelling}
                    className="h-8 text-red-600 border-red-200 hover:bg-red-50"
                  >
                    <X className="w-3.5 h-3.5 mr-1.5" />
                    {isCancelling ? 'Cancelling...' : 'Cancel'}
                  </Button>
                </>
              )}
              {isPaused && (
                <>
                  <Button
                    size="sm"
                    onClick={handleResume}
                    disabled={isResuming}
                    className="h-8"
                  >
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    {isResuming ? 'Resuming...' : 'Resume'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    disabled={isCancelling}
                    className="h-8 text-red-600 border-red-200 hover:bg-red-50"
                  >
                    <X className="w-3.5 h-3.5 mr-1.5" />
                    {isCancelling ? 'Cancelling...' : 'Cancel'}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </CardContent>

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </Card>
  )
}
