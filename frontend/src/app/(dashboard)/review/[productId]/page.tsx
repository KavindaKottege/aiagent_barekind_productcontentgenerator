import { Metadata } from 'next'
import { redirect, notFound } from 'next/navigation'
import { getReviewProduct, getReviewProducts } from '@/app/actions/review'
import { ReviewInterface } from '@/components/review/review-interface'
import { ReviewProvider } from '@/lib/review-context'

export const metadata: Metadata = {
  title: 'Review Product - Product Content Generator',
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

  // Fetch product and all products in parallel for navigation
  const [product, allProducts] = await Promise.all([
    getReviewProduct(clientId, productId),
    getReviewProducts(clientId),
  ])

  if (!product) {
    notFound()
  }

  // Extract product IDs for navigation
  const allProductIds = allProducts.map(p => p.id)

  return (
    <ReviewProvider>
      <ReviewInterface
        product={product}
        clientId={clientId}
        allProductIds={allProductIds}
      />
    </ReviewProvider>
  )
}
