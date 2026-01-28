'use client'

import { useSelectedClient } from '@/lib/client-context'
import { UploadModal } from './upload-modal'

interface Client {
  id: string
  brand_name: string
}

interface UploadButtonWrapperProps {
  clients: Client[]
}

export function UploadButtonWrapper({ clients }: UploadButtonWrapperProps) {
  const { selectedClientId } = useSelectedClient()

  const selectedClient = clients.find(c => c.id === selectedClientId)

  return (
    <UploadModal
      selectedClientId={selectedClientId}
      selectedClientName={selectedClient?.brand_name || null}
      hasExistingProducts={!!selectedClientId}  // Show warning whenever a client is selected
    />
  )
}
