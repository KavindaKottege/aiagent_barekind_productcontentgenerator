'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useSelectedClient } from '@/lib/client-context'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ReviewStatsComponent } from '@/components/review/review-stats'
import { AIReviewProgress } from '@/components/review/ai-review-progress'
import { Sparkles } from 'lucide-react'
import {
  startBatchAIReview,
  getBatchAIReviewStatus,
  ProductGroupReview,
  ReviewStats,
} from '@/app/actions/review'
import {
  getActiveJobForClient,
  GenerationJob,
  GenerationProgress,
} from '@/app/actions/generation'

interface ReviewPageClientProps {
  clientId: string | null
  accessToken: string
  stats: ReviewStats | null
  products: ProductGroupReview[]
  firstUnreviewed: ProductGroupReview | undefined
  statusFilter: string
}

export function ReviewPageClient({
  clientId,
  accessToken,
  stats: initialStats,
  products: initialProducts,
  firstUnreviewed,
  statusFilter,
}: ReviewPageClientProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { selectedClientId } = useSelectedClient()
  const [showModeToggle, setShowModeToggle] = useState(false)
  const [autoApproveMode, setAutoApproveMode] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [hasActiveJob, setHasActiveJob] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Real-time generation monitoring state
  const [products, setProducts] = useState(initialProducts)
  const [stats, setStats] = useState(initialStats)
  const [activeGenerationJob, setActiveGenerationJob] = useState<GenerationJob | null>(null)
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null)
  const lastRefreshRef = useRef<number>(0)
  const REFRESH_DEBOUNCE_MS = 2000

  // Sync URL with selected client from context (same pattern as products page)
  useEffect(() => {
    const urlClientId = searchParams.get('client')

    if (selectedClientId && selectedClientId !== urlClientId) {
      // Update URL when client changes
      router.push(`/review?client=${selectedClientId}`)
    }
  }, [selectedClientId, searchParams, router])

  // Refresh products list from server
  const refreshProducts = useCallback(async () => {
    if (!clientId) return
    try {
      const response = await fetch(`/api/review/products?clientId=${clientId}`, {
        cache: 'no-store',
      })
      if (response.ok) {
        const data = await response.json()
        setProducts(data.products || [])
        setStats(data.stats || initialStats)
      }
    } catch (error) {
      console.error('Failed to refresh products:', error)
    }
  }, [clientId, initialStats])

  // Check for active AI review job on mount
  useEffect(() => {
    if (!clientId) return
    const checkActiveJob = async () => {
      const status = await getBatchAIReviewStatus(clientId)
      if (status && (status.status === 'running' || status.status === 'paused')) {
        setHasActiveJob(true)
      }
    }
    checkActiveJob()
  }, [clientId])

  // Check for active generation job on mount
  useEffect(() => {
    if (!clientId) return
    const checkActiveGeneration = async () => {
      const result = await getActiveJobForClient(clientId)
      if (result.success && result.job) {
        setActiveGenerationJob(result.job)
      }
    }
    checkActiveGeneration()
  }, [clientId])

  // SSE connection for real-time generation progress
  useEffect(() => {
    if (!activeGenerationJob || !accessToken) return

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const eventSource = new EventSource(
      `${apiUrl}/api/generation/jobs/${activeGenerationJob.id}/progress?token=${accessToken}`
    )

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data) as GenerationProgress
      setGenerationProgress(data)

      // Debounced refresh: only refresh if enough time has passed
      const now = Date.now()
      if (now - lastRefreshRef.current > REFRESH_DEBOUNCE_MS) {
        lastRefreshRef.current = now
        refreshProducts()
      }
    })

    eventSource.addEventListener('complete', () => {
      // Always refresh on complete for final product list
      refreshProducts()
      setActiveGenerationJob(null)
      setGenerationProgress(null)
      eventSource.close()
    })

    eventSource.addEventListener('error', (event) => {
      console.error('Generation SSE error:', event)
    })

    return () => {
      eventSource.close()
    }
  }, [activeGenerationJob, accessToken, refreshProducts])

  const handleShowModeToggle = () => {
    setShowModeToggle(true)
    setError(null)
  }

  const handleStartBatchReview = async () => {
    if (!clientId) return
    setIsStarting(true)
    setError(null)

    const result = await startBatchAIReview(clientId, autoApproveMode)

    if ('error' in result) {
      setError(result.error)
      setIsStarting(false)
    } else {
      setHasActiveJob(true)
      setShowModeToggle(false)
    }
  }

  const handleComplete = () => {
    setHasActiveJob(false)
    router.refresh()
  }

  // Update firstUnreviewed based on current products state
  const currentFirstUnreviewed = products.find(p => !p.review_status)

  // Show empty state when no client is selected (will redirect via useEffect when context has client)
  if (!clientId) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Review Products</h2>
        </div>
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-gray-600">
              Select a client from the dropdown in the header to review their products.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Review Products</h2>
          <p className="text-gray-600 mt-1">Review and approve AI-generated content</p>
        </div>

        {/* Review All with AI button */}
        {products.length > 0 && !hasActiveJob && !activeGenerationJob && (
          <Button onClick={handleShowModeToggle} className="gap-2">
            <Sparkles className="w-4 h-4" />
            Review All with AI
          </Button>
        )}
      </div>

      {/* Generation in progress banner */}
      {activeGenerationJob && generationProgress && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-blue-900">
                  Generation in progress
                </p>
                <p className="text-sm text-blue-700 mt-1">
                  {generationProgress.completed} of {generationProgress.total} products complete
                  {' · '}
                  {stats?.pending_review ?? 0} ready for review
                </p>
              </div>
              <div className="flex gap-2">
                <Badge className="bg-blue-600">
                  {Math.round((generationProgress.completed / generationProgress.total) * 100)}% complete
                </Badge>
                {currentFirstUnreviewed && (
                  <Link href={`/review/${currentFirstUnreviewed.id}?client=${clientId}`}>
                    <Button size="sm">
                      Start Reviewing
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mode Toggle Dialog */}
      {showModeToggle && !hasActiveJob && (
        <Card className="border-2 border-blue-500">
          <CardContent className="pt-6 space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Choose AI Review Mode</h3>
              <p className="text-sm text-gray-600 mb-4">
                Select how AI should handle product reviews
              </p>
            </div>

            {/* Mode selector */}
            <div className="space-y-3">
              <label className="flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="mode"
                  checked={!autoApproveMode}
                  onChange={() => setAutoApproveMode(false)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <div className="font-semibold">AI-assisted mode (Recommended)</div>
                  <div className="text-sm text-gray-600">
                    AI will provide recommendations for each product. You make the final approval decision.
                  </div>
                </div>
              </label>

              <label className="flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="mode"
                  checked={autoApproveMode}
                  onChange={() => setAutoApproveMode(true)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <div className="font-semibold">AI-auto mode</div>
                  <div className="text-sm text-gray-600">
                    AI will automatically approve or reject products. You can override any decision.
                  </div>
                </div>
              </label>
            </div>

            {/* Error display */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                onClick={() => setShowModeToggle(false)}
                disabled={isStarting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleStartBatchReview}
                disabled={isStarting}
                className="flex-1"
              >
                {isStarting ? 'Starting...' : 'Start AI Review'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Review Progress */}
      {hasActiveJob && (
        <AIReviewProgress
          clientId={clientId}
          accessToken={accessToken}
          onComplete={handleComplete}
        />
      )}

      {/* Review Stats Bar */}
      {stats && (
        <ReviewStatsComponent
          stats={stats}
          onFilterClick={(status) => {
            // This will be handled client-side in future enhancement
            // For now, filter via URL params
          }}
        />
      )}

      {/* Empty State */}
      {products.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600 text-lg mb-4">
              No products ready for review.
            </p>
            <p className="text-gray-500 mb-6">
              Generate content first from the Products page.
            </p>
            <Link href={`/products?client=${clientId}`}>
              <Button>Go to Products</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Start Review Button */}
      {products.length > 0 && currentFirstUnreviewed && !hasActiveJob && !activeGenerationJob && (
        <div className="flex justify-center">
          <Link href={`/review/${currentFirstUnreviewed.id}?client=${clientId}`}>
            <Button size="lg" className="px-8">
              Start Review
            </Button>
          </Link>
        </div>
      )}

      {/* Product Grid */}
      {products.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product) => {
            const displayTitle = product.edited_title || product.generated_title || product.product_name
            const statusBadge = product.review_status || 'pending'

            return (
              <Card key={product.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {/* Thumbnail */}
                  {product.images.length > 0 ? (
                    <div className="w-full h-40 mb-3 bg-gray-100 rounded overflow-hidden">
                      <img
                        src={product.images[0]}
                        alt={product.product_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23f3f4f6" width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%239ca3af" font-family="sans-serif"%3ENo Image%3C/text%3E%3C/svg%3E'
                        }}
                      />
                    </div>
                  ) : (
                    <div className="w-full h-40 mb-3 bg-gray-100 rounded flex items-center justify-center">
                      <span className="text-gray-400">No image</span>
                    </div>
                  )}

                  {/* Product Name */}
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                    {product.product_name}
                  </h3>

                  {/* Generated Title Preview */}
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {displayTitle}
                  </p>

                  {/* Status Badge */}
                  <div className="flex items-center justify-between">
                    <Badge
                      variant={
                        statusBadge === 'approved' ? 'default' :
                        statusBadge === 'rejected' ? 'destructive' :
                        statusBadge === 'edited' ? 'secondary' :
                        statusBadge === 'ai_approved' ? 'default' :
                        statusBadge === 'ai_rejected' ? 'destructive' :
                        'outline'
                      }
                      className={
                        statusBadge === 'ai_approved' ? 'bg-purple-600' :
                        statusBadge === 'ai_rejected' ? 'bg-purple-600' :
                        ''
                      }
                    >
                      {statusBadge === 'approved' ? 'Approved' :
                       statusBadge === 'rejected' ? 'Rejected' :
                       statusBadge === 'edited' ? 'Edited' :
                       statusBadge === 'ai_approved' ? 'AI Approved' :
                       statusBadge === 'ai_rejected' ? 'AI Rejected' :
                       'Pending Review'}
                    </Badge>

                    {/* Review Link */}
                    <Link href={`/review/${product.id}?client=${clientId}`}>
                      <Button variant="ghost" size="sm">
                        Review
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
