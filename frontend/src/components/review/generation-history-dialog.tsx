'use client'

import { useState, useEffect, useTransition } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { History, Check, RotateCcw } from 'lucide-react'
import {
  GenerationHistoryItem,
  getGenerationHistory,
  restoreVersion,
} from '@/app/actions/regeneration'

interface GenerationHistoryDialogProps {
  productGroupId: string
  open: boolean
  onClose: () => void
  onRestore: () => void // Called after successful restore
}

export function GenerationHistoryDialog({
  productGroupId,
  open,
  onClose,
  onRestore,
}: GenerationHistoryDialogProps) {
  const [history, setHistory] = useState<GenerationHistoryItem[]>([])
  const [productName, setProductName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  // Fetch history when dialog opens
  useEffect(() => {
    if (open) {
      setIsLoading(true)
      setError(null)
      getGenerationHistory(productGroupId).then((data) => {
        if (data) {
          setHistory(data.history)
          setProductName(data.product_name)
        } else {
          setError('Failed to load history')
        }
        setIsLoading(false)
      })
    }
  }, [open, productGroupId])

  const handleRestore = async (auditId: string) => {
    startTransition(async () => {
      setError(null)
      const result = await restoreVersion(productGroupId, auditId)
      if (result.success) {
        onRestore()
        onClose()
      } else {
        setError(result.message)
      }
    })
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Generation History
          </DialogTitle>
          <DialogDescription>
            {productName ? `${productName} - ` : ''}
            {history.length} version{history.length !== 1 ? 's' : ''} available
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="py-8 text-center text-gray-500">Loading history...</div>
        ) : history.length === 0 ? (
          <div className="py-8 text-center text-gray-500">No generation history found</div>
        ) : (
          <ScrollArea className="max-h-[50vh] pr-4">
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border ${
                    item.is_current
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-200 bg-white hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {item.is_current && (
                          <Badge variant="outline" className="text-green-700 border-green-300">
                            <Check className="w-3 h-3 mr-1" />
                            Current
                          </Badge>
                        )}
                        <Badge variant="secondary">
                          {item.regeneration_number === 0
                            ? 'Original'
                            : `Regeneration #${item.regeneration_number}`}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {formatDate(item.created_at)}
                        </span>
                        <span className="text-xs text-gray-500">{item.cost}</span>
                      </div>

                      <div className="space-y-2">
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase">
                            Title
                          </span>
                          <p className="text-sm text-gray-900 truncate">
                            {item.title || '(no title)'}
                          </p>
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase">
                            Description
                          </span>
                          <p className="text-sm text-gray-700 line-clamp-2">
                            {item.description
                              ? item.description.slice(0, 150) + (item.description.length > 150 ? '...' : '')
                              : '(no description)'}
                          </p>
                        </div>
                      </div>
                    </div>

                    {!item.is_current && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRestore(item.id)}
                        disabled={isPending}
                        className="flex-shrink-0"
                      >
                        <RotateCcw className="w-4 h-4 mr-1" />
                        Restore
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  )
}
