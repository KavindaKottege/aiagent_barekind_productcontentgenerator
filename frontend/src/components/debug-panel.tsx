'use client'

import { useDebug } from '@/lib/debug-context'
import { useSelectedClient } from '@/lib/client-context'
import { useState, useEffect, useRef, useCallback } from 'react'
import { Bug, ChevronDown, ChevronUp, Trash2, GripHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getDebugToken, type DebugLogEntry } from '@/app/actions/debug'

const HEIGHT_STORAGE_KEY = 'debugPanelHeight'
const MIN_HEIGHT = 120
const MAX_HEIGHT = 800
const DEFAULT_HEIGHT = 320

function parsePromptUsed(promptUsed: string): { system: string; user: string } {
  const systemMatch = promptUsed.match(
    /\[system\]\s*([\s\S]*?)(?=\[(?:human|user)\]|$)/
  )
  const userMatch = promptUsed.match(/\[(?:human|user)\]\s*([\s\S]*)$/)
  return {
    system: systemMatch?.[1]?.trim() || '',
    user: userMatch?.[1]?.trim() || '',
  }
}

function LogDetail({ log }: { log: DebugLogEntry }) {
  const { system, user } = parsePromptUsed(log.prompt_used)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span
          className={`font-bold ${log.success ? 'text-green-400' : 'text-red-400'}`}
        >
          Attempt #{log.attempt_number} &mdash;{' '}
          {log.success ? 'Success' : 'Failed'}
        </span>
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-gray-400">
        <span>
          Model: <span className="text-gray-200">{log.model_version}</span>
        </span>
        <span>
          Temperature: <span className="text-gray-200">{log.temperature}</span>
        </span>
        <span>
          Cost: <span className="text-gray-200">${log.cost}</span>
        </span>
        <span>
          Duration: <span className="text-gray-200">{log.duration_ms}ms</span>
        </span>
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-gray-400">
        <span>
          Input tokens:{' '}
          <span className="text-gray-200">{log.input_tokens}</span>
        </span>
        <span>
          Output tokens:{' '}
          <span className="text-gray-200">{log.output_tokens}</span>
        </span>
      </div>

      {log.error_message && (
        <div className="rounded border border-red-800 bg-red-950 p-2 text-xs text-red-300">
          {log.error_message}
        </div>
      )}

      <details open>
        <summary className="cursor-pointer text-xs font-semibold text-blue-400 mb-1">
          System Prompt ({system.length} chars)
        </summary>
        <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap rounded border border-gray-800 bg-gray-950 p-2 text-xs text-gray-300">
          {system}
        </pre>
      </details>

      <details open>
        <summary className="cursor-pointer text-xs font-semibold text-green-400 mb-1">
          User Prompt ({user.length} chars)
        </summary>
        <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap rounded border border-gray-800 bg-gray-950 p-2 text-xs text-gray-300">
          {user}
        </pre>
      </details>

      {(log.generated_title || log.generated_description) && (
        <details>
          <summary className="cursor-pointer text-xs font-semibold text-orange-400 mb-1">
            Generated Output
          </summary>
          <div className="space-y-1 text-xs text-gray-300">
            {log.generated_title && (
              <div>
                <span className="text-gray-500">Title:</span>{' '}
                {log.generated_title}
                {log.title_length != null && (
                  <span className="text-gray-500">
                    {' '}
                    ({log.title_length} chars)
                  </span>
                )}
              </div>
            )}
            {log.generated_description && (
              <div>
                <span className="text-gray-500">Description:</span>{' '}
                {log.generated_description.length > 200
                  ? log.generated_description.slice(0, 200) + '...'
                  : log.generated_description}
                {log.description_length != null && (
                  <span className="text-gray-500">
                    {' '}
                    ({log.description_length} chars)
                  </span>
                )}
              </div>
            )}
          </div>
        </details>
      )}
    </div>
  )
}

export function DebugPanel() {
  const { isDebugEnabled, debugLogs, addLogs, clearLogs, isAdmin } = useDebug()
  const { selectedClientId } = useSelectedClient()
  const [isExpanded, setIsExpanded] = useState(true)
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [panelHeight, setPanelHeight] = useState(DEFAULT_HEIGHT)
  const scrollRef = useRef<HTMLDivElement>(null)
  const lastTimestamp = useRef<string | null>(null)
  const prevClientId = useRef<string | null>(null)
  const isDragging = useRef(false)
  const dragStartY = useRef(0)
  const dragStartHeight = useRef(0)

  // Load saved height from sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem(HEIGHT_STORAGE_KEY)
    if (saved) {
      const h = parseInt(saved, 10)
      if (h >= MIN_HEIGHT && h <= MAX_HEIGHT) setPanelHeight(h)
    }
  }, [])

  // Get access token on mount
  useEffect(() => {
    if (!isAdmin) return
    getDebugToken().then((token) => {
      if (token) setAccessToken(token)
    })
  }, [isAdmin])

  // Reset lastTimestamp when client changes
  useEffect(() => {
    if (prevClientId.current !== selectedClientId) {
      lastTimestamp.current = null
      prevClientId.current = selectedClientId
    }
  }, [selectedClientId])

  // Poll for debug logs
  useEffect(() => {
    if (!isDebugEnabled || !selectedClientId || !accessToken) return

    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    const poll = async () => {
      try {
        let url = `${apiUrl}/api/debug/logs/client/${selectedClientId}/latest`
        const params: string[] = []
        if (lastTimestamp.current) {
          params.push(`since=${encodeURIComponent(lastTimestamp.current)}`)
        }
        params.push('limit=50')
        url += '?' + params.join('&')

        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
          cache: 'no-store',
        })

        if (response.ok) {
          const entries: DebugLogEntry[] = await response.json()
          if (entries.length > 0) {
            addLogs(entries)
            lastTimestamp.current = entries[entries.length - 1].created_at
          }
        }
      } catch {
        // Silently ignore polling errors
      }
    }

    poll()
    const interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [isDebugEnabled, selectedClientId, accessToken, addLogs])

  // Auto-scroll when new logs arrive
  useEffect(() => {
    if (isExpanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [debugLogs.length, isExpanded])

  // Drag resize handlers
  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      isDragging.current = true
      dragStartY.current = e.clientY
      dragStartHeight.current = panelHeight
      document.body.style.cursor = 'row-resize'
      document.body.style.userSelect = 'none'

      const handleDragMove = (ev: MouseEvent) => {
        if (!isDragging.current) return
        const delta = dragStartY.current - ev.clientY
        const newHeight = Math.max(
          MIN_HEIGHT,
          Math.min(MAX_HEIGHT, dragStartHeight.current + delta)
        )
        setPanelHeight(newHeight)
      }

      const handleDragEnd = () => {
        if (!isDragging.current) return
        isDragging.current = false
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        // Save on release
        const delta = dragStartY.current - 0 // just save current
        // Read from state via DOM to get the latest
        document.removeEventListener('mousemove', handleDragMove)
        document.removeEventListener('mouseup', handleDragEnd)
      }

      document.addEventListener('mousemove', handleDragMove)
      document.addEventListener('mouseup', handleDragEnd)
    },
    [panelHeight]
  )

  // Persist height when it changes (debounced via drag end)
  useEffect(() => {
    sessionStorage.setItem(HEIGHT_STORAGE_KEY, String(panelHeight))
  }, [panelHeight])

  if (!isDebugEnabled) return null

  const selectedLog = selectedLogId
    ? debugLogs.find((l) => l.id === selectedLogId) || null
    : null

  return (
    <div
      className="flex flex-col border-t-2 border-orange-500/50 bg-gray-900 text-gray-100"
      style={{ height: isExpanded ? panelHeight : 'auto' }}
    >
      {/* Drag handle */}
      {isExpanded && (
        <div
          className="flex h-2 cursor-row-resize items-center justify-center bg-gray-800 hover:bg-gray-700 transition-colors"
          onMouseDown={handleDragStart}
        >
          <GripHorizontal className="h-3 w-5 text-gray-500" />
        </div>
      )}

      {/* Header bar */}
      <div
        className="flex shrink-0 cursor-pointer select-none items-center justify-between bg-gray-800/90 px-4 py-1.5 backdrop-blur"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Bug className="h-4 w-4 text-orange-400" />
          <span className="font-mono text-sm font-semibold text-orange-300">
            Debug Mode
          </span>
          <Badge
            variant="outline"
            className="border-gray-600 text-xs text-gray-400"
          >
            {debugLogs.length} entries
          </Badge>
          {selectedClientId && isDebugEnabled && (
            <Badge className="animate-pulse border-0 bg-green-900 text-xs text-green-300">
              Polling
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            className="h-6 text-gray-400 hover:text-white"
            onClick={(e) => {
              e.stopPropagation()
              clearLogs()
              setSelectedLogId(null)
              lastTimestamp.current = null
            }}
          >
            <Trash2 className="mr-1 h-3 w-3" /> Clear
          </Button>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronUp className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* Log content */}
      {isExpanded && (
        <div className="flex min-h-0 flex-1">
          {/* Left: Log list */}
          <div
            ref={scrollRef}
            className="w-1/3 overflow-y-auto border-r border-gray-700"
          >
            {debugLogs.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-gray-500">
                No debug logs yet. Start a generation to see prompts.
              </div>
            ) : (
              debugLogs.map((log) => (
                <div
                  key={log.id}
                  className={`cursor-pointer border-b border-gray-800 px-3 py-2 text-xs hover:bg-gray-800/50 ${
                    selectedLogId === log.id
                      ? 'border-l-2 border-l-orange-400 bg-gray-800'
                      : ''
                  }`}
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedLogId(log.id)
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={
                        log.success ? 'text-green-400' : 'text-red-400'
                      }
                    >
                      {log.success ? 'OK' : 'FAIL'} #{log.attempt_number}
                    </span>
                    <span className="text-gray-500">{log.duration_ms}ms</span>
                  </div>
                  <div className="mt-0.5 truncate text-gray-400">
                    {log.model_version} | temp={log.temperature} | ${log.cost}
                  </div>
                  <div className="mt-0.5 truncate text-gray-500">
                    Tokens: {log.input_tokens} in / {log.output_tokens} out
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right: Selected log detail */}
          <div className="flex-1 overflow-y-auto p-4">
            {selectedLog ? (
              <LogDetail log={selectedLog} />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-gray-500">
                Select a log entry to view prompt details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
