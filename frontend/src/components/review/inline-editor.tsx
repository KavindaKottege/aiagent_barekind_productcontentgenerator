'use client'

import { useState, useRef, useLayoutEffect, KeyboardEvent } from 'react'

interface InlineEditorProps {
  value: string
  onSave: (value: string) => Promise<void>
  minChars: number
  maxChars: number
  placeholder: string
  multiline: boolean
}

export function InlineEditor({ value, onSave, minChars, maxChars, placeholder, multiline }: InlineEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(value)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const divRef = useRef<HTMLDivElement>(null)

  // Sync editValue when value prop changes
  useLayoutEffect(() => {
    if (!isEditing) {
      setEditValue(value)
    }
  }, [value, isEditing])

  // Focus and place cursor at end when entering edit mode
  useLayoutEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus()
      const length = textareaRef.current.value.length
      textareaRef.current.setSelectionRange(length, length)
    }
  }, [isEditing])

  const charCount = editValue.length
  const isInRange = charCount >= minChars && charCount <= maxChars
  const counterColor = isInRange ? 'text-green-600' : 'text-red-600'

  const handleClick = () => {
    if (!isEditing) {
      setIsEditing(true)
      setError(null)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditValue(value)
    setError(null)
  }

  const handleSave = async () => {
    // Validate character limits
    if (!isInRange) {
      setError(`Content must be between ${minChars} and ${maxChars} characters (currently ${charCount})`)
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      await onSave(editValue)
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      handleCancel()
    } else if (e.key === 'Enter' && !multiline) {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Enter' && e.ctrlKey && multiline) {
      e.preventDefault()
      handleSave()
    }
  }

  if (isEditing) {
    return (
      <div className="space-y-2">
        <textarea
          ref={textareaRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSaving}
          placeholder={placeholder}
          className={`w-full px-3 py-2 border rounded-md font-mono text-sm ${
            isSaving ? 'bg-gray-50 cursor-wait' : 'bg-white'
          } ${
            error ? 'border-red-500' : 'border-gray-300 focus:border-blue-500'
          } text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-200 resize-none`}
          rows={multiline ? 12 : 2}
        />

        {/* Character counter */}
        <div className="flex items-center justify-between">
          <span className={`text-xs font-medium ${counterColor}`}>
            {charCount}/{minChars}-{maxChars} characters
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              Cancel (Esc)
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !isInRange}
              className="px-3 py-1 text-sm bg-brand-blue text-white hover:bg-brand-blue-hover rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : multiline ? 'Save (Ctrl+Enter)' : 'Save (Enter)'}
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }

  return (
    <div
      ref={divRef}
      onClick={handleClick}
      className="group cursor-text border border-gray-200 rounded-md px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors relative"
    >
      <div
        className={`text-sm font-mono whitespace-pre-wrap ${value ? 'text-gray-900' : 'text-gray-400'} ${
          multiline ? 'max-h-[300px] overflow-y-auto' : ''
        }`}
      >
        {value || placeholder}
      </div>

      {/* Character counter - always visible */}
      <div className="mt-2 text-xs text-gray-500">
        {charCount}/{minChars}-{maxChars} characters
      </div>

      {/* Hover hint */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="text-xs text-gray-400 bg-white px-2 py-1 rounded border border-gray-200">
          Click to edit
        </span>
      </div>
    </div>
  )
}
