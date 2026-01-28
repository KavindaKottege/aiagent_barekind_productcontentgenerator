import { Metadata } from 'next'
import { redirect, notFound } from 'next/navigation'
import { getReviewProduct, getReviewProducts } from '@/app/actions/review'
import { getClient } from '@/app/actions/clients'
import { getTaskSettings } from '@/app/actions/settings'
import { ReviewInterface } from '@/components/review/review-interface'
import { ReviewProvider } from '@/lib/review-context'

export const metadata: Metadata = {
  title: 'Review Product - SEO Content Generator',
  description: 'Review and approve generated product content',
}

interface ReviewProductPageProps {
  params: Promise<{ productId: string }>
  searchParams: Promise<{ client?: string }>
}

export default async function ReviewProductPage({ params, searchParams }: ReviewProductPageProps) {
  const { productId } = await params
  const { client: clientId } = await searchParams

  if (!clientId) {
    redirect('/review')
  }

  // Fetch product, all products, client, and task settings in parallel
  const [product, allProducts, client, taskSettings] = await Promise.all([
    getReviewProduct(clientId, productId),
    getReviewProducts(clientId),
    getClient(clientId),
    getTaskSettings(),
  ])

  if (!product) {
    notFound()
  }

  // Extract product IDs for navigation
  const allProductIds = allProducts.map(p => p.id)

  // Get selected AI input fields (default to all fields if not set)
  const selectedFields = client?.ai_input_fields || []

  return (
    <ReviewProvider>
      <ReviewInterface
        product={product}
        clientId={clientId}
        allProductIds={allProductIds}
        selectedFields={selectedFields}
        titleMinChars={taskSettings?.task1_min_length ?? undefined}
        titleMaxChars={taskSettings?.task1_max_length ?? undefined}
        descMinChars={taskSettings?.task2_min_length ?? undefined}
        descMaxChars={taskSettings?.task2_max_length ?? undefined}
      />
    </ReviewProvider>
  )
}
