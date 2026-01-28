'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useSelectedClient } from '@/lib/client-context'

interface Client {
  id: string
  brand_name: string
  has_custom_prompts: boolean
}

interface ClientSelectorProps {
  clients: Client[]
}

export function ClientSelector({ clients }: ClientSelectorProps) {
  const { selectedClientId, setSelectedClientId, isLoading } = useSelectedClient()
  const router = useRouter()

  // Auto-select first client if none selected and clients exist
  useEffect(() => {
    if (!isLoading && !selectedClientId && clients.length > 0) {
      setSelectedClientId(clients[0].id)
    }
  }, [isLoading, selectedClientId, clients, setSelectedClientId])

  // Clear selection if selected client no longer exists
  useEffect(() => {
    if (!isLoading && selectedClientId && clients.length > 0) {
      const exists = clients.some(c => c.id === selectedClientId)
      if (!exists) {
        setSelectedClientId(clients[0]?.id || null)
      }
    }
  }, [isLoading, selectedClientId, clients, setSelectedClientId])

  // Show loading placeholder during hydration
  if (isLoading) {
    return (
      <div className="w-[200px] h-10 bg-gray-100 rounded-md animate-pulse" />
    )
  }

  // Show empty state if no clients
  if (clients.length === 0) {
    return (
      <button
        onClick={() => router.push('/clients/new')}
        className="text-sm text-brand-blue hover:text-brand-blue-hover hover:underline"
      >
        + Create your first client
      </button>
    )
  }

  return (
    <Select value={selectedClientId || undefined} onValueChange={setSelectedClientId}>
      <SelectTrigger className="w-[200px] bg-white text-gray-900 border-gray-300">
        <SelectValue placeholder="Select client" />
      </SelectTrigger>
      <SelectContent>
        {clients.map((client) => (
          <SelectItem key={client.id} value={client.id}>
            <div className="flex items-center gap-2">
              <span>{client.brand_name}</span>
              {client.has_custom_prompts && (
                <Badge variant="secondary" className="text-xs">Custom</Badge>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
