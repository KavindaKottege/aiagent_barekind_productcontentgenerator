import { Metadata } from 'next'
import { getProductGroups, ProductGroup } from '@/app/actions/products'
import { getClient, Client } from '@/app/actions/clients'
import { ProductsPageContent } from '@/components/products-page-content'

export const metadata: Metadata = {
  title: 'Products - SEO Content Generator',
  description: 'Manage uploaded products',
}

interface ProductsPageProps {
  searchParams: Promise<{ client?: string }>
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = await searchParams
  const clientId = params.client || null

  let groups: ProductGroup[] = []
  let client: Client | null = null

  if (clientId) {
    try {
      // Fetch products and client in parallel
      // getClient already exists from Phase 2 - it fetches a single client by ID
      [groups, client] = await Promise.all([
        getProductGroups(clientId),
        getClient(clientId),
      ])
    } catch (e) {
      console.error('Failed to load products:', e)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Products</h2>
      </div>
      <ProductsPageContent
        initialGroups={groups}
        clientId={clientId}
        client={client}
      />
    </div>
  )
}
