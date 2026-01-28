'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Package, X, Play, RefreshCw, RotateCcw } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ProductGroup } from '@/app/actions/products'

interface ProductVariant {
  id: string
  option_type: string | null  // e.g., "Color"
  option_name: string | null  // e.g., "Black"
  status: string | null
  description: string | null
  images: string[] | null
  row_index: number
}

interface ProductGroupCardProps {
  group: ProductGroup
  onFetchVariants?: (groupId: string) => Promise<ProductVariant[]>
  onGenerateProduct?: (groupId: string) => Promise<void>
  isGenerationActive?: boolean
}

export function ProductGroupCard({ group, onFetchVariants, onGenerateProduct, isGenerationActive }: ProductGroupCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [variants, setVariants] = useState<ProductVariant[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  const handleExpand = async (open: boolean) => {
    console.log('[ProductGroupCard] handleExpand called:', open, 'group:', group.product_name)
    setIsExpanded(open)

    // Lazy load variants on first expand
    if (open && !variants && onFetchVariants) {
      console.log('[ProductGroupCard] Fetching variants for:', group.id)
      setIsLoading(true)
      try {
        const fetchedVariants = await onFetchVariants(group.id)
        console.log('[ProductGroupCard] Got variants:', fetchedVariants)
        setVariants(fetchedVariants)
      } catch (error) {
        console.error('[ProductGroupCard] Error fetching variants:', error)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const statusColor = {
    pending: 'bg-gray-100 text-gray-800',
    generated: 'bg-brand-blue-light text-brand-blue',
    approved: 'bg-brand-green-light text-brand-green-hover',
    rejected: 'bg-red-100 text-red-800',
    failed: 'bg-orange-100 text-orange-800',
  }[group.status] || 'bg-gray-100 text-gray-800'

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => {
          console.log('[ProductGroupCard] Card clicked!')
          handleExpand(!isExpanded)
        }}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="h-6 w-6 p-0 mt-0.5 flex items-center justify-center text-gray-600">
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </div>
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
          <div className="flex items-center gap-2">
            {/* Generate/Regenerate/Retry button */}
            {onGenerateProduct && !isGenerationActive && (
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs"
                onClick={(e) => {
                  e.stopPropagation()
                  onGenerateProduct(group.id)
                }}
              >
                {group.status === 'pending' ? (
                  <>
                    <Play className="h-3 w-3 mr-1" />
                    Generate
                  </>
                ) : group.status === 'failed' ? (
                  <>
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Retry
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Regenerate
                  </>
                )}
              </Button>
            )}
            <Badge className={statusColor}>
              {group.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 border-t border-gray-200 bg-gray-50">
          {isLoading ? (
            <div className="py-4 text-center text-sm text-gray-500">
              Loading...
            </div>
          ) : variants && variants.length > 0 ? (
            <div className="py-3 space-y-4">
              {/* Image and Description from first variant */}
              <div className="flex gap-4">
                {/* Thumbnail image */}
                {variants[0].images && variants[0].images.length > 0 && (
                  <div className="flex-shrink-0">
                    <img
                      src={variants[0].images[0]}
                      alt={group.product_name}
                      className="w-20 h-20 object-cover rounded-md border border-gray-200 cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation()
                        setPreviewImage(variants[0].images![0])
                      }}
                      onError={(e) => {
                        // Hide broken images
                        (e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                  </div>
                )}

                {/* Existing description */}
                {variants[0].description && (
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                      Existing Description
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-4">
                      {variants[0].description}
                    </p>
                  </div>
                )}
              </div>

              {/* Variant options (only show if more than 1) */}
              {variants.length > 1 && (
                <div>
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                    {variants.length} Variants
                  </div>
                  <ul className="space-y-1">
                    {variants.map((variant) => (
                      <li
                        key={variant.id}
                        className="flex items-center text-sm py-1.5 px-2 rounded hover:bg-white"
                      >
                        {variant.option_type && (
                          <span className="text-gray-500 mr-1">
                            {variant.option_type}:
                          </span>
                        )}
                        <span className="text-gray-700">
                          {variant.option_name || 'Default'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="py-4 text-center text-sm text-gray-500">
              No details available
            </div>
          )}

          {group.generated_title && (
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Generated Title
                </div>
                <div className="text-xs text-gray-400 font-mono">
                  {group.generated_title.length} chars
                </div>
              </div>
              <p className="text-sm text-gray-900">{group.generated_title}</p>
            </div>
          )}

          {group.generated_description && (
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Generated Description
                </div>
                <div className="text-xs text-gray-400 font-mono">
                  {group.generated_description.length} chars
                </div>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap overflow-y-auto" style={{ maxHeight: '4.5rem' }}>
                {group.generated_description}
              </p>
            </div>
          )}
        </CardContent>
      )}

      {/* Image Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          onClick={() => setPreviewImage(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh] p-2">
            <button
              className="absolute -top-2 -right-2 z-10 bg-white rounded-full p-1 shadow-lg hover:bg-gray-100"
              onClick={(e) => {
                e.stopPropagation()
                setPreviewImage(null)
              }}
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
            <img
              src={previewImage}
              alt={group.product_name}
              className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </Card>
  )
}
