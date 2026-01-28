'use client'

import { useState, useTransition } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { updateClientFieldSelection } from '@/app/actions/clients'

// Available product fields that can be used for AI generation
// These match the attributes used in Task 1 (title) and Task 2 (description) prompts
const AVAILABLE_FIELDS = [
  { id: 'product_name', label: 'Product Name', required: true, description: 'Base product name' },
  { id: 'description', label: 'Original Description', required: false, description: 'Existing product description' },
  { id: 'country_of_origin', label: 'Country of Origin', required: false, description: 'Where product is made' },
  { id: 'images', label: 'Image URLs', required: false, description: 'Product images (for reference)' },
] as const

const REQUIRED_FIELDS: string[] = AVAILABLE_FIELDS.filter(f => f.required).map(f => f.id)

interface FieldSelectionPanelProps {
  clientId: string
  currentSelection: string[] | null
  onSelectionChange?: () => void
}

export function FieldSelectionPanel({
  clientId,
  currentSelection,
  onSelectionChange,
}: FieldSelectionPanelProps) {
  // Filter saved selection to only include valid field IDs (handles old 8-field selections)
  const validFieldIds: string[] = AVAILABLE_FIELDS.map(f => f.id)
  const defaultSelection = currentSelection
    ? currentSelection.filter(id => validFieldIds.includes(id))
    : validFieldIds

  const [selectedFields, setSelectedFields] = useState<string[]>(defaultSelection)
  const [isPending, startTransition] = useTransition()
  const [saved, setSaved] = useState(false)

  const handleToggle = (fieldId: string, checked: boolean) => {
    // Don't allow unchecking required fields
    if (!checked && REQUIRED_FIELDS.includes(fieldId)) {
      return
    }

    setSelectedFields(prev =>
      checked
        ? [...prev, fieldId]
        : prev.filter(f => f !== fieldId)
    )
    setSaved(false)
  }

  const handleSave = () => {
    startTransition(async () => {
      const result = await updateClientFieldSelection(clientId, selectedFields)
      if (result.success) {
        setSaved(true)
        onSelectionChange?.()
        // Reset saved indicator after 2 seconds
        setTimeout(() => setSaved(false), 2000)
      }
    })
  }

  const hasChanges = JSON.stringify(selectedFields.sort()) !== JSON.stringify((currentSelection || defaultSelection).sort())

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">AI Input Fields</CardTitle>
        <p className="text-sm text-gray-500">
          Select which product fields to include in AI generation prompts.
          More context helps create better content.
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {AVAILABLE_FIELDS.map((field) => (
            <div key={field.id} className="flex items-start space-x-3">
              <Checkbox
                id={field.id}
                checked={selectedFields.includes(field.id)}
                onCheckedChange={(checked) => handleToggle(field.id, !!checked)}
                disabled={field.required}
              />
              <div className="space-y-0.5">
                <label
                  htmlFor={field.id}
                  className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 ${
                    field.required ? 'text-gray-500' : 'text-gray-900 cursor-pointer'
                  }`}
                >
                  {field.label}
                  {field.required && (
                    <span className="ml-1 text-xs text-gray-400">(required)</span>
                  )}
                </label>
                <p className="text-xs text-gray-500">{field.description}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {selectedFields.length} of {AVAILABLE_FIELDS.length} fields selected
          </div>
          <div className="flex items-center gap-3">
            {saved && (
              <span className="text-sm text-green-600">Saved!</span>
            )}
            <Button
              onClick={handleSave}
              disabled={isPending || !hasChanges}
              size="sm"
            >
              {isPending ? 'Saving...' : 'Save Selection'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
