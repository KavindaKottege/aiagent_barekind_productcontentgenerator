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
import { History, Check, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react'
import {
  GenerationHistoryItem,
  getGenerationHistory,
  restoreVersion,
} from '@/app/actions/regeneration'

const VISIBLE_COUNT = 3

interface GenerationHistoryDialogProps {
  productGroupId: string
  open: boolean
  onClose: () => void
  onRestore: () => void
}

function HistoryRow({
  item,
  versionLabel,
  isPending,
  onRestore,
}: {
  item: GenerationHistoryItem
  versionLabel: string
  isPending: boolean
  onRestore: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

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
    <div
      className={`border rounded-lg overflow-hidden ${
        item.is_current ? 'border-green-300 bg-green-50/50' : 'border-gray-200'
      }`}
    >
      {/* Compact row */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
        )}

        <Badge
          variant={item.is_current ? 'default' : 'secondary'}
          className={`text-xs flex-shrink-0 ${
            item.is_current ? 'bg-green-600' : ''
          }`}
        >
          {versionLabel}
        </Badge>

        <span className="text-sm text-gray-900 truncate flex-1 min-w-0">
          {item.title || '(no title)'}
        </span>

        <span className="text-xs text-gray-400 flex-shrink-0 whitespace-nowrap">
          {formatDate(item.created_at)}
        </span>

        <span className="text-xs text-gray-400 flex-shrink-0 w-16 text-right">
          {item.cost}
        </span>

        {item.is_current ? (
          <Badge variant="outline" className="text-green-700 border-green-300 text-xs flex-shrink-0">
            <Check className="w-3 h-3 mr-1" />
            Current
          </Badge>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              onRestore(item.id)
            }}
            disabled={isPending}
            className="flex-shrink-0 h-7 text-xs px-2"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Restore
          </Button>
        )}
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-gray-100 bg-gray-50/30">
          <div className="grid grid-cols-1 gap-3 text-sm">
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Title
              </span>
              <p className="text-gray-900 mt-0.5">
                {item.title || '(no title)'}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Description
              </span>
              <p className="text-gray-700 mt-0.5 whitespace-pre-line text-xs leading-relaxed max-h-40 overflow-y-auto">
                {item.description || '(no description)'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
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
  const [showOlder, setShowOlder] = useState(false)

  useEffect(() => {
    if (open) {
      setIsLoading(true)
      setError(null)
      setShowOlder(false)
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

  const handleRestore = (auditId: string) => {
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

  // Version labels: v1 (oldest) to vN (newest)
  const getVersionLabel = (index: number) => {
    const versionNum = history.length - index
    if (versionNum === 1) return 'v1'
    return `v${versionNum}`
  }

  const recentItems = history.slice(0, VISIBLE_COUNT)
  const olderItems = history.slice(VISIBLE_COUNT)
  const hasOlder = olderItems.length > 0

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Generation History
          </DialogTitle>
          <DialogDescription>
            {productName ? `${productName} — ` : ''}
            {history.length} version{history.length !== 1 ? 's' : ''}
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
          <ScrollArea className="max-h-[55vh]">
            <div className="space-y-1.5 pr-4">
              {/* Recent versions (always visible) */}
              {recentItems.map((item, index) => (
                <HistoryRow
                  key={item.id}
                  item={item}
                  versionLabel={getVersionLabel(index)}
                  isPending={isPending}
                  onRestore={handleRestore}
                />
              ))}

              {/* Older versions (collapsible) */}
              {hasOlder && (
                <>
                  <button
                    onClick={() => setShowOlder(!showOlder)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    {showOlder ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                    <span>
                      {olderItems.length} older version{olderItems.length !== 1 ? 's' : ''}
                    </span>
                  </button>

                  {showOlder &&
                    olderItems.map((item, index) => (
                      <HistoryRow
                        key={item.id}
                        item={item}
                        versionLabel={getVersionLabel(VISIBLE_COUNT + index)}
                        isPending={isPending}
                        onRestore={handleRestore}
                      />
                    ))}
                </>
              )}
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  )
}
