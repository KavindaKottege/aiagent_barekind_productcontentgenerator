'use client'

// Placeholder for Task 3 - will implement full functionality
interface InlineEditorProps {
  value: string
  onSave: (value: string) => Promise<void>
  minChars: number
  maxChars: number
  placeholder: string
  multiline: boolean
}

export function InlineEditor({ value, minChars, maxChars, placeholder, multiline }: InlineEditorProps) {
  return (
    <div className="border rounded p-3 bg-gray-50">
      <p className="text-sm text-gray-900 whitespace-pre-wrap">
        {value || placeholder}
      </p>
      <p className="text-xs text-gray-500 mt-2">
        {value.length}/{minChars}-{maxChars} chars
      </p>
    </div>
  )
}
