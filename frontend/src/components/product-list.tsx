'use client'

import { useState, useMemo } from 'react'
import { ProductGroup } from '@/app/actions/products'
import { ProductGroupCard } from './product-group-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface ProductVariant {
  id: string
  option_type: string | null  // e.g., "Color"
  option_name: string | null  // e.g., "Black"
  status: string | null
  description: string | null
  images: string[] | null
  row_index: number
}

interface ProductListProps {
  groups: ProductGroup[]
  onGenerateProduct?: (groupId: string) => Promise<void>
  isGenerationActive?: boolean
}

// Available statuses for filtering
const STATUSES = ['all', 'pending', 'generated', 'failed', 'approved', 'rejected'] as const
type StatusFilter = typeof STATUSES[number]

export function ProductList({ groups, onGenerateProduct, isGenerationActive }: ProductListProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  const handleFetchVariants = async (groupId: string): Promise<ProductVariant[]> => {
    // Client-side fetch to Next.js API route
    try {
      console.log('[ProductList] Fetching variants for group:', groupId)
      const response = await fetch(`/api/products/groups/${groupId}`)
      console.log('[ProductList] Response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('[ProductList] Fetch failed:', errorData)
        return []
      }

      const data = await response.json()
      console.log('[ProductList] Received data:', data)
      console.log('[ProductList] Variants:', data.variants)
      return data.variants || []
    } catch (error) {
      console.error('[ProductList] Exception:', error)
      return []
    }
  }

  // Filter groups by status (EXCL-04: User can filter products by status)
  const filteredGroups = useMemo(() => {
    if (statusFilter === 'all') return groups
    return groups.filter(g => g.status === statusFilter)
  }, [groups, statusFilter])

  // Count by status for filter badges
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: groups.length }
    for (const group of groups) {
      counts[group.status] = (counts[group.status] || 0) + 1
    }
    return counts
  }, [groups])

  if (groups.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-4xl mb-4">...</div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          No products yet
        </h3>
        <p className="text-gray-500">
          Upload a Faire Excel file to import products.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status Filter (EXCL-04) */}
      <div className="flex items-center gap-2 pb-2">
        <span className="text-sm text-gray-500 mr-2">Filter by status:</span>
        {STATUSES.map((status) => (
          <Button
            key={status}
            variant={statusFilter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(status)}
            className="capitalize"
          >
            {status}
            {statusCounts[status] !== undefined && (
              <Badge variant="secondary" className="ml-1.5 text-xs">
                {statusCounts[status]}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* Filtered Results */}
      {filteredGroups.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No products with status &quot;{statusFilter}&quot;
        </div>
      ) : (
        <div className="space-y-3">
          {filteredGroups.map((group) => (
            <ProductGroupCard
              key={group.id}
              group={group}
              onFetchVariants={handleFetchVariants}
              onGenerateProduct={onGenerateProduct}
              isGenerationActive={isGenerationActive}
            />
          ))}
        </div>
      )}
    </div>
  )
}
