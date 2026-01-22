'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Package } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { ProductGroup } from '@/app/actions/products'

interface ProductVariant {
  id: string
  option_name: string | null
  status: string | null
  row_index: number
}

interface ProductGroupCardProps {
  group: ProductGroup
  onFetchVariants?: (groupId: string) => Promise<ProductVariant[]>
}

export function ProductGroupCard({ group, onFetchVariants }: ProductGroupCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [variants, setVariants] = useState<ProductVariant[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleExpand = async (open: boolean) => {
    setIsExpanded(open)

    // Lazy load variants on first expand
    if (open && !variants && onFetchVariants) {
      setIsLoading(true)
      try {
        const fetchedVariants = await onFetchVariants(group.id)
        setVariants(fetchedVariants)
      } catch (error) {
        console.error('Error fetching variants:', error)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const statusColor = {
    pending: 'bg-gray-100 text-gray-800',
    generated: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  }[group.status] || 'bg-gray-100 text-gray-800'

  return (
    <Card className="overflow-hidden">
      <Collapsible open={isExpanded} onOpenChange={handleExpand}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-gray-50 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 mt-0.5"
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
                <div className="space-y-1">
                  <h3 className="font-medium text-gray-900 leading-tight">
                    {group.product_name}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span>SKU: {group.sku}</span>
                    {group.variant_count > 1 && (
                      <>
                        <span className="text-gray-300">|</span>
                        <span className="flex items-center gap-1">
                          <Package className="h-3 w-3" />
                          {group.variant_count} options
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <Badge className={statusColor}>
                {group.status}
              </Badge>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 border-t bg-gray-50">
            {isLoading ? (
              <div className="py-4 text-center text-sm text-gray-500">
                Loading variants...
              </div>
            ) : variants && variants.length > 0 ? (
              <div className="py-3 space-y-2">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Product Options
                </div>
                <ul className="space-y-1">
                  {variants.map((variant) => (
                    <li
                      key={variant.id}
                      className="flex items-center justify-between text-sm py-1.5 px-2 rounded hover:bg-white"
                    >
                      <span className="text-gray-700">
                        {variant.option_name || 'Default'}
                      </span>
                      {variant.status && (
                        <span className="text-xs text-gray-400">
                          {variant.status}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="py-4 text-center text-sm text-gray-500">
                No variant details available
              </div>
            )}

            {group.generated_title && (
              <div className="border-t pt-3 mt-3">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  Generated Title
                </div>
                <p className="text-sm text-gray-900">{group.generated_title}</p>
              </div>
            )}

            {group.generated_description && (
              <div className="border-t pt-3 mt-3">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  Generated Description
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {group.generated_description.slice(0, 300)}
                  {group.generated_description.length > 300 && '...'}
                </p>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
