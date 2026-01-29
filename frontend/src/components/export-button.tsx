'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Download } from 'lucide-react'
import { useSelectedClient } from '@/lib/client-context'
import { ExportDialog } from '@/components/export-dialog'

interface Client {
  id: string
  brand_name: string
}

interface ExportButtonProps {
  clients: Client[]
}

export function ExportButton({ clients }: ExportButtonProps) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const { selectedClientId } = useSelectedClient()

  const isDisabled = !selectedClientId || selectedClientId === 'all'
  const selectedClient = clients.find((c) => c.id === selectedClientId)

  if (isDisabled) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span tabIndex={0}>
              <Button variant="outline" size="sm" disabled className="bg-white/10 border-white/20 text-gray-400">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <p>Select a client to export</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setDialogOpen(true)}
        className="bg-white/10 border-white/20 text-white hover:bg-white/20"
      >
        <Download className="h-4 w-4 mr-2" />
        Export
      </Button>

      {selectedClient && (
        <ExportDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          clientId={selectedClient.id}
          clientName={selectedClient.brand_name}
        />
      )}
    </>
  )
}
