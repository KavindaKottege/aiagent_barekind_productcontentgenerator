import { Metadata } from 'next'
import { getProductGroups, ProductGroup } from '@/app/actions/products'
import { ProductsPageContent } from '@/components/products-page-content'

export const metadata: Metadata = {
  title: 'Products - Product Content Generator',
  description: 'Manage uploaded products',
}

interface ProductsPageProps {
  searchParams: Promise<{ client?: string }>
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = await searchParams
  const clientId = params.client || null

  let groups: ProductGroup[] = []

  if (clientId) {
    try {
      groups = await getProductGroups(clientId)
    } catch (e) {
      console.error('Failed to load products:', e)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Products</h2>
      </div>
      <ProductsPageContent initialGroups={groups} clientId={clientId} />
    </div>
  )
}
