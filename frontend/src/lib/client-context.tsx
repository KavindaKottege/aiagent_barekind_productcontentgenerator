'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'

interface ClientContextType {
  selectedClientId: string | null
  setSelectedClientId: (id: string | null) => void
  isLoading: boolean
}

const ClientContext = createContext<ClientContextType>({
  selectedClientId: null,
  setSelectedClientId: () => {},
  isLoading: true,
})

const STORAGE_KEY = 'selectedClientId'

export function ClientProvider({ children }: { children: React.ReactNode }) {
  const [selectedClientId, setSelectedClientIdState] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load from localStorage on mount (client-side only)
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      setSelectedClientIdState(stored)
    }
    setIsLoading(false)
  }, [])

  // Sync to localStorage on change
  const setSelectedClientId = useCallback((id: string | null) => {
    setSelectedClientIdState(id)
    if (id) {
      localStorage.setItem(STORAGE_KEY, id)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  return (
    <ClientContext.Provider value={{ selectedClientId, setSelectedClientId, isLoading }}>
      {children}
    </ClientContext.Provider>
  )
}

export function useSelectedClient() {
  const context = useContext(ClientContext)
  if (context === undefined) {
    throw new Error('useSelectedClient must be used within a ClientProvider')
  }
  return context
}
