'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useSelectedClient } from '@/lib/client-context'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ProductList } from './product-list'
import { ProductGroup } from '@/app/actions/products'

interface ProductsPageContentProps {
  initialGroups: ProductGroup[]
  clientId: string | null
}

export function ProductsPageContent({
  initialGroups,
  clientId,
}: ProductsPageContentProps) {
  const { selectedClientId } = useSelectedClient()
  const router = useRouter()
  const searchParams = useSearchParams()

  // Sync URL with selected client
  useEffect(() => {
    const urlClientId = searchParams.get('client')

    if (selectedClientId && selectedClientId !== urlClientId) {
      // Update URL when client changes
      router.push(`/products?client=${selectedClientId}`)
    }
  }, [selectedClientId, searchParams, router])

  const groups = initialGroups

  if (!clientId && !selectedClientId) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-gray-600">
            Select a client from the dropdown in the header to view their products,
            or upload a new Excel file.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      {/* Stats Header */}
      {groups.length > 0 && (
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-gray-600">
              {groups.length} product groups uploaded
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline">
              {groups.filter(g => g.status === 'pending').length} pending
            </Badge>
            <Badge variant="outline">
              {groups.filter(g => g.variant_count > 1).length} with variants
            </Badge>
          </div>
        </div>
      )}
      <ProductList groups={groups} />
    </>
  )
}
