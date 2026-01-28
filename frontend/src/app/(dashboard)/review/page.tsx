import { Metadata } from 'next'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { cookies } from 'next/headers'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ReviewStatsComponent } from '@/components/review/review-stats'
import { getReviewProducts, getReviewStats } from '@/app/actions/review'
import { ReviewPageClient } from './review-page-client'

export const metadata: Metadata = {
  title: 'Review Products - SEO Content Generator',
  description: 'Review and approve generated product content',
}

interface ReviewPageProps {
  searchParams: Promise<{ client?: string; status?: string }>
}

export default async function ReviewPage({ searchParams }: ReviewPageProps) {
  const params = await searchParams
  const clientId = params.client || null
  const statusFilter = params.status || 'all'

  // Get access token for SSE
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value || ''

  // If no client selected, render client component which will sync with context
  if (!clientId) {
    return (
      <ReviewPageClient
        clientId={null}
        accessToken={accessToken}
        stats={null}
        products={[]}
        firstUnreviewed={undefined}
        statusFilter={statusFilter}
      />
    )
  }

  // Fetch stats and products in parallel
  const [stats, products] = await Promise.all([
    getReviewStats(clientId),
    getReviewProducts(clientId, statusFilter),
  ])

  // Find first unreviewed product for "Start Review" button
  // Pending = review_status is null
  const firstUnreviewed = products.find(p => !p.review_status)

  return (
    <ReviewPageClient
      clientId={clientId}
      accessToken={accessToken}
      stats={stats}
      products={products}
      firstUnreviewed={firstUnreviewed}
      statusFilter={statusFilter}
    />
  )
}

// Extracted server component content
function ReviewPageServerContent({
  stats,
  products,
  firstUnreviewed,
  clientId,
  statusFilter,
}: {
  stats: any
  products: any[]
  firstUnreviewed: any
  clientId: string
  statusFilter: string
}) {
  return (
    <>
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
      {products.length > 0 && firstUnreviewed && (
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
                        'outline'
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
    </>
  )
}
