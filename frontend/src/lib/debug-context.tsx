'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { DebugLogEntry } from '@/app/actions/debug'

interface DebugContextType {
  isDebugEnabled: boolean
  setDebugEnabled: (enabled: boolean) => void
  debugLogs: DebugLogEntry[]
  addLogs: (newLogs: DebugLogEntry[]) => void
  clearLogs: () => void
  activeJobId: string | null
  setActiveJobId: (jobId: string | null) => void
  isAdmin: boolean
}

const DebugContext = createContext<DebugContextType>({
  isDebugEnabled: false,
  setDebugEnabled: () => {},
  debugLogs: [],
  addLogs: () => {},
  clearLogs: () => {},
  activeJobId: null,
  setActiveJobId: () => {},
  isAdmin: false,
})

const STORAGE_KEY = 'debugModeEnabled'
const MAX_LOGS = 500

export function DebugProvider({
  children,
  isAdmin,
}: {
  children: React.ReactNode
  isAdmin: boolean
}) {
  const [isDebugEnabled, setDebugEnabledState] = useState(false)
  const [debugLogs, setDebugLogs] = useState<DebugLogEntry[]>([])
  const [activeJobId, setActiveJobIdState] = useState<string | null>(null)

  // Load from sessionStorage on mount (admin only)
  useEffect(() => {
    if (!isAdmin) return
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored === 'true') {
      setDebugEnabledState(true)
    }
  }, [isAdmin])

  const setDebugEnabled = useCallback((enabled: boolean) => {
    setDebugEnabledState(enabled)
    sessionStorage.setItem(STORAGE_KEY, String(enabled))
    if (!enabled) {
      setDebugLogs([])
    }
  }, [])

  const addLogs = useCallback((newLogs: DebugLogEntry[]) => {
    setDebugLogs((prev) => {
      const existingIds = new Set(prev.map((l) => l.id))
      const unique = newLogs.filter((l) => !existingIds.has(l.id))
      if (unique.length === 0) return prev
      return [...prev, ...unique].slice(-MAX_LOGS)
    })
  }, [])

  const clearLogs = useCallback(() => {
    setDebugLogs([])
  }, [])

  const setActiveJobId = useCallback((jobId: string | null) => {
    setActiveJobIdState(jobId)
  }, [])

  // Non-admin: render children without debug capability
  if (!isAdmin) {
    return <>{children}</>
  }

  return (
    <DebugContext.Provider
      value={{
        isDebugEnabled,
        setDebugEnabled,
        debugLogs,
        addLogs,
        clearLogs,
        activeJobId,
        setActiveJobId,
        isAdmin,
      }}
    >
      {children}
    </DebugContext.Provider>
  )
}

export function useDebug() {
  const context = useContext(DebugContext)
  return context
}
