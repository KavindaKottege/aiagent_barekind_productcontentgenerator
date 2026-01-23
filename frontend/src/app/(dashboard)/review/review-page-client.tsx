'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
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

interface ReviewPageClientProps {
  clientId: string
  accessToken: string
  stats: ReviewStats
  products: ProductGroupReview[]
  firstUnreviewed: ProductGroupReview | undefined
  statusFilter: string
}

export function ReviewPageClient({
  clientId,
  accessToken,
  stats,
  products,
  firstUnreviewed,
  statusFilter,
}: ReviewPageClientProps) {
  const router = useRouter()
  const [showModeToggle, setShowModeToggle] = useState(false)
  const [autoApproveMode, setAutoApproveMode] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [hasActiveJob, setHasActiveJob] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check for active job on mount
  useEffect(() => {
    const checkActiveJob = async () => {
      const status = await getBatchAIReviewStatus(clientId)
      if (status && (status.status === 'running' || status.status === 'paused')) {
        setHasActiveJob(true)
      }
    }
    checkActiveJob()
  }, [clientId])

  const handleShowModeToggle = () => {
    setShowModeToggle(true)
    setError(null)
  }

  const handleStartBatchReview = async () => {
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Review Products</h2>
          <p className="text-gray-600 mt-1">Review and approve AI-generated content</p>
        </div>

        {/* Review All with AI button */}
        {products.length > 0 && !hasActiveJob && (
          <Button onClick={handleShowModeToggle} className="gap-2">
            <Sparkles className="w-4 h-4" />
            Review All with AI
          </Button>
        )}
      </div>

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
      <ReviewStatsComponent
        stats={stats}
        onFilterClick={(status) => {
          // This will be handled client-side in future enhancement
          // For now, filter via URL params
        }}
      />

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
      {products.length > 0 && firstUnreviewed && !hasActiveJob && (
        <div className="flex justify-center">
          <Link href={`/review/${firstUnreviewed.id}?client=${clientId}`}>
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
