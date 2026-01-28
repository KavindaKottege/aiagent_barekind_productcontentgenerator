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
import { ProductGroup, getProductGroups } from '@/app/actions/products'
import { Client } from '@/app/actions/clients'
import {
  startGeneration,
  getActiveJobForClient,
  retryFailedProducts,
  generateSingleProduct,
  GenerationJob,
} from '@/app/actions/generation'

interface ProductsPageContentProps {
  initialGroups: ProductGroup[]
  clientId: string | null
  client: Client | null
}

export function ProductsPageContent({
  initialGroups,
  clientId,
  client,
}: ProductsPageContentProps) {
  const { selectedClientId } = useSelectedClient()
  const router = useRouter()
  const searchParams = useSearchParams()

  const [groups, setGroups] = useState<ProductGroup[]>(initialGroups)
  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Update groups when initialGroups changes (e.g., from navigation)
  useEffect(() => {
    setGroups(initialGroups)
  }, [initialGroups])

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

  // Periodically refresh product groups while generation is running
  // This keeps the product list badges in sync with actual database state
  useEffect(() => {
    if (!activeJob || activeJob.status !== 'running' || !clientId) return

    const interval = setInterval(async () => {
      const updatedGroups = await getProductGroups(clientId)
      setGroups(updatedGroups)
    }, 3000) // Refresh every 3 seconds

    return () => clearInterval(interval)
  }, [activeJob, clientId])

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

  const handleGenerationComplete = useCallback(async (newJob?: GenerationJob) => {
    // If a new job is provided (e.g., from soft cap continue), switch to it directly
    if (newJob) {
      setActiveJob(newJob)
      // Still refresh product groups to show updated statuses
      if (clientId) {
        const updatedGroups = await getProductGroups(clientId)
        setGroups(updatedGroups)
      }
      return
    }

    // Original behavior for terminal states
    if (clientId) {
      const updatedGroups = await getProductGroups(clientId)
      setGroups(updatedGroups)

      // Check if there's a new active job (e.g., from resume)
      const jobResult = await getActiveJobForClient(clientId)
      if (jobResult.success && jobResult.job) {
        setActiveJob(jobResult.job)
      } else {
        setActiveJob(null)
      }
    } else {
      setActiveJob(null)
    }
    router.refresh()
  }, [clientId, router])

  const pendingCount = groups.filter((g) => g.status === 'pending').length
  const failedCount = groups.filter((g) => g.status === 'failed').length

  const handleRetryFailed = useCallback(async () => {
    if (!clientId) return

    setIsStarting(true)
    setError(null)

    const result = await retryFailedProducts(clientId)

    setIsStarting(false)

    if (result.success && result.job) {
      setActiveJob(result.job)
    } else {
      setError(result.error || 'Failed to retry failed products')
    }
  }, [clientId])

  const handleGenerateSingle = useCallback(async (productGroupId: string) => {
    setIsStarting(true)
    setError(null)

    const result = await generateSingleProduct(productGroupId)

    setIsStarting(false)

    if (result.success && result.job) {
      setActiveJob(result.job)
    } else {
      setError(result.error || 'Failed to generate product')
    }
  }, [])

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
      {activeJob && (
        <GenerationProgress
          key={activeJob.id}
          jobId={activeJob.id}
          initialJob={activeJob}
          onComplete={handleGenerationComplete}
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

            {/* Retry Failed button - show when no active job and has failed products */}
            {!activeJob && failedCount > 0 && (
              <Button
                onClick={handleRetryFailed}
                disabled={isStarting}
                variant="outline"
                className="ml-2"
              >
                {isStarting ? 'Starting...' : `Retry ${failedCount} Failed`}
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
      <ProductList
        groups={groups}
        onGenerateProduct={handleGenerateSingle}
        isGenerationActive={!!activeJob}
      />
    </div>
  )
}
