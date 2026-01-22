'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useSelectedClient } from '@/lib/client-context'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ProductList } from './product-list'
import { FieldSelectionPanel } from './field-selection-panel'
import { ProductGroup } from '@/app/actions/products'
import { Client } from '@/app/actions/clients'

interface ProductsPageContentProps {
  initialGroups: ProductGroup[]
  clientId: string | null
  client: Client | null
}

export function ProductsPageContent({
  initialGroups,
  clientId,
  client,
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
    <div className="space-y-6">
      {/* Field Selection Panel - only show when products exist */}
      {clientId && client && groups.length > 0 && (
        <FieldSelectionPanel
          clientId={clientId}
          currentSelection={client.ai_input_fields}
          onSelectionChange={() => router.refresh()}
        />
      )}

      {/* Stats Header */}
      {groups.length > 0 && (
        <div className="flex items-center justify-between">
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

      {/* Product List */}
      <ProductList groups={groups} />
    </div>
  )
}
