'use client'

import { useState } from 'react'
import { AlertTriangle, ChevronDown } from 'lucide-react'
import { ProductGroupReview } from '@/app/actions/review'

interface MissingFieldsWarningProps {
  product: ProductGroupReview
  selectedFields: string[]
}

// Field mapping: selected field name -> how to check if present in product
const FIELD_CHECKERS: Record<string, (product: ProductGroupReview) => boolean> = {
  product_name: (p) => !!p.product_name, // Always present
  description: (p) => !!p.original_data.description,
  product_type: (p) => !!p.original_data.product_type,
  option_name: (p) => !!p.original_data.option_name,
  country_of_origin: (p) => !!p.original_data.country_of_origin,
  made_to_order: (p) => !!p.original_data.made_to_order,
  sku: (p) => !!p.sku, // Always present
  images: (p) => p.images.length > 0,
}

// Human-readable field names
const FIELD_LABELS: Record<string, string> = {
  product_name: 'Product Name',
  description: 'Original Description',
  product_type: 'Product Type',
  option_name: 'Option Name',
  country_of_origin: 'Country of Origin',
  made_to_order: 'Made to Order',
  sku: 'SKU',
  images: 'Images',
}

export function MissingFieldsWarning({ product, selectedFields }: MissingFieldsWarningProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Check which selected fields are missing in the product
  const missingFields: string[] = []

  for (const fieldName of selectedFields) {
    const checker = FIELD_CHECKERS[fieldName]
    if (checker && !checker(product)) {
      missingFields.push(fieldName)
    }
  }

  // If no missing fields, don't render anything
  if (missingFields.length === 0) {
    return null
  }

  return (
    <div className="bg-amber-50 border border-amber-300 rounded-lg overflow-hidden">
      {/* Warning Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center gap-3 hover:bg-amber-100 transition-colors"
      >
        <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
        <div className="flex-1 text-left">
          <p className="font-semibold text-amber-900">
            This product is missing {missingFields.length} AI input field{missingFields.length > 1 ? 's' : ''}
          </p>
          <p className="text-sm text-amber-700 mt-0.5">
            Click to see details
          </p>
        </div>
        <ChevronDown
          className={`w-5 h-5 text-amber-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Expandable Details */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-amber-200">
          <p className="text-sm text-amber-800 mb-3">
            The AI generated content without these fields, which may affect quality:
          </p>
          <ul className="space-y-2">
            {missingFields.map((fieldName) => (
              <li key={fieldName} className="flex items-start gap-2 text-sm">
                <span className="text-amber-600 mt-0.5">•</span>
                <div>
                  <span className="font-semibold text-amber-900">
                    {FIELD_LABELS[fieldName] || fieldName}:
                  </span>
                  <span className="text-amber-700 ml-1">
                    Not provided in original data
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
