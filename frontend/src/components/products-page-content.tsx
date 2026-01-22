'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useSelectedClient } from '@/lib/client-context'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ProductList } from './product-list'
import { FieldSelectionPanel } from './field-selection-panel'
import { GenerationProgress } from './generation-progress'
import { ProductGroup } from '@/app/actions/products'
import { Client } from '@/app/actions/clients'
import {
  startGeneration,
  getActiveJobForClient,
  GenerationJob,
} from '@/app/actions/generation'

interface ProductsPageContentProps {
  initialGroups: ProductGroup[]
  clientId: string | null
  client: Client | null
  accessToken: string | null
}

export function ProductsPageContent({
  initialGroups,
  clientId,
  client,
  accessToken,
}: ProductsPageContentProps) {
  const { selectedClientId } = useSelectedClient()
  const router = useRouter()
  const searchParams = useSearchParams()

  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sync URL with selected client
  useEffect(() => {
    const urlClientId = searchParams.get('client')

    if (selectedClientId && selectedClientId !== urlClientId) {
      // Update URL when client changes
      router.push(`/products?client=${selectedClientId}`)
    }
  }, [selectedClientId, searchParams, router])

  // Check for active job on mount and when client changes
  useEffect(() => {
    async function checkActiveJob() {
      if (clientId) {
        const result = await getActiveJobForClient(clientId)
        if (result.success && result.job) {
          setActiveJob(result.job)
        } else {
          setActiveJob(null)
        }
      }
    }
    checkActiveJob()
  }, [clientId])

  const handleStartGeneration = useCallback(async () => {
    if (!clientId) return

    setIsStarting(true)
    setError(null)

    const result = await startGeneration(clientId)

    setIsStarting(false)

    if (result.success && result.job) {
      setActiveJob(result.job)
    } else {
      setError(result.error || 'Failed to start generation')
    }
  }, [clientId])

  const handleGenerationComplete = useCallback(() => {
    setActiveJob(null)
    router.refresh() // Refresh to update product statuses
  }, [router])

  const groups = initialGroups
  const pendingCount = groups.filter((g) => g.status === 'pending').length

  if (!clientId && !selectedClientId) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-gray-600">
            Select a client from the dropdown in the header to view their products,
            or upload a new Excel file.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Active generation progress */}
      {activeJob && accessToken && (
        <GenerationProgress
          jobId={activeJob.id}
          initialJob={activeJob}
          onComplete={handleGenerationComplete}
          accessToken={accessToken}
        />
      )}

      {/* Field Selection Panel - only show when products exist and no active job */}
      {clientId && client && groups.length > 0 && !activeJob && (
        <FieldSelectionPanel
          clientId={clientId}
          currentSelection={client.ai_input_fields}
          onSelectionChange={() => router.refresh()}
        />
      )}

      {/* Stats Header with Generate Button */}
      {groups.length > 0 && (
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600">{groups.length} product groups uploaded</p>
          </div>
          <div className="flex gap-2 items-center">
            <Badge variant="outline">
              {pendingCount} pending
            </Badge>
            <Badge variant="outline">
              {groups.filter((g) => g.status === 'generated').length} generated
            </Badge>
            <Badge variant="outline">
              {groups.filter((g) => g.variant_count > 1).length} with variants
            </Badge>

            {/* Generate button - show when no active job and has pending products */}
            {!activeJob && pendingCount > 0 && (
              <Button
                onClick={handleStartGeneration}
                disabled={isStarting}
                className="ml-4"
              >
                {isStarting ? 'Starting...' : `Generate ${pendingCount} Products`}
              </Button>
            )}

            {/* Block message when generation is running */}
            {activeJob && activeJob.status === 'running' && (
              <Badge variant="secondary" className="ml-4">
                Generation in progress...
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Product List */}
      <ProductList groups={groups} />
    </div>
  )
}
