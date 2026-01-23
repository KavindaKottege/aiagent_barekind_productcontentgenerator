'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, CheckCircle, XCircle, Sparkles } from 'lucide-react'
import { ProductGroupReview, requestAIReview } from '@/app/actions/review'
import { useRouter } from 'next/navigation'

interface AIReviewPanelProps {
  product: ProductGroupReview
  onAIReviewComplete?: () => void
}

export function AIReviewPanel({ product, onAIReviewComplete }: AIReviewPanelProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasAIReview = product.ai_review_status !== null
  const aiApproved = product.ai_review_status === 'ai_approved'
  const aiRejected = product.ai_review_status === 'ai_rejected'

  const handleRequestReview = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await requestAIReview(product.id)

      if (!result) {
        setError('Failed to get AI review. Please try again.')
        setIsLoading(false)
        return
      }

      // Refresh to get updated product data
      router.refresh()

      if (onAIReviewComplete) {
        onAIReviewComplete()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  // Helper to format safety flag descriptions
  const getSafetyFlagDescription = (flag: string): string => {
    switch (flag) {
      case 'quantity_confusion':
        return 'Possible confusion about quantity or set size'
      case 'misleading_expectations':
        return 'Content may set incorrect expectations'
      case 'misrepresentation':
        return 'Title may not accurately represent product'
      default:
        return flag.replace(/_/g, ' ')
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-600" />
            AI Review
          </CardTitle>
          {hasAIReview && (
            <Badge
              variant={aiApproved ? 'default' : aiRejected ? 'destructive' : 'outline'}
              className={aiApproved ? 'bg-green-600' : ''}
            >
              {aiApproved ? 'AI Approved' : aiRejected ? 'AI Rejected' : product.ai_review_status}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* No AI review yet */}
        {!hasAIReview && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Get AI feedback to check for accuracy and safety concerns.
            </p>
            <Button
              onClick={handleRequestReview}
              disabled={isLoading}
              className="w-full"
              variant="outline"
            >
              {isLoading ? (
                <>
                  <span className="animate-pulse">Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Get AI Feedback
                </>
              )}
            </Button>
          </div>
        )}

        {/* AI review exists */}
        {hasAIReview && (
          <div className="space-y-4">
            {/* Recommendation badge and reason */}
            <div className="flex items-start gap-2">
              {aiApproved ? (
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 line-clamp-3">
                  {product.ai_review_reason || 'No reason provided'}
                </p>
              </div>
            </div>

            {/* Confidence level */}
            {product.ai_review_status && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Confidence</span>
                  <span className="font-semibold text-gray-900">
                    {aiApproved ? 'High' : 'Review needed'}
                  </span>
                </div>
              </div>
            )}

            {/* Safety flags section */}
            {product.ai_review_safety_flags && product.ai_review_safety_flags.length > 0 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <span className="text-sm font-semibold text-orange-900">
                    Safety Concerns
                  </span>
                </div>
                <ul className="space-y-1 text-sm text-orange-800">
                  {product.ai_review_safety_flags.map((flag, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-orange-600 mt-0.5">•</span>
                      <span>{getSafetyFlagDescription(flag)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleRequestReview}
                disabled={isLoading}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                {isLoading ? 'Re-analyzing...' : 'Re-run AI Review'}
              </Button>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Timestamp */}
        {product.ai_reviewed_at && (
          <p className="text-xs text-gray-500 pt-2 border-t">
            Reviewed: {new Date(product.ai_reviewed_at).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
