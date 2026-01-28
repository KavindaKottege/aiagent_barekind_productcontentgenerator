'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types matching backend schemas
export interface GenerationHistoryItem {
  id: string
  title: string | null
  description: string | null
  created_at: string
  cost: string
  attempt_number: number
  regeneration_number: number
  is_current: boolean
}

export interface GenerationHistoryResponse {
  product_group_id: string
  product_name: string
  current_title: string | null
  current_description: string | null
  history: GenerationHistoryItem[]
}

export interface RegenerationEstimate {
  rejected_count: number
  estimated_cost: string
}

export interface RegenerationJobResponse {
  job_id: string
  status: string
  total_count: number
  is_regeneration: boolean
  message: string
}

async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies()
  return cookieStore.get('access_token')?.value || null
}

/**
 * Get generation history for a product
 */
export async function getGenerationHistory(
  productGroupId: string
): Promise<GenerationHistoryResponse | null> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${API_URL}/api/regeneration/${productGroupId}/history`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      console.error(`Failed to fetch history: ${response.status}`)
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching history:', error)
    return null
  }
}

/**
 * Restore a previous version as current
 */
export async function restoreVersion(
  productGroupId: string,
  auditId: string
): Promise<{ success: boolean; message: string }> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, message: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${API_URL}/api/regeneration/${productGroupId}/restore/${auditId}`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to restore' }))
      return { success: false, message: errorData.detail || errorData.message }
    }

    return { success: true, message: 'Version restored successfully' }
  } catch (error) {
    console.error('Error restoring version:', error)
    return { success: false, message: 'Network error' }
  }
}

/**
 * Get estimate for batch regeneration
 */
export async function getRegenerationEstimate(
  clientId: string
): Promise<RegenerationEstimate | null> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${API_URL}/api/regeneration/${clientId}/estimate`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching estimate:', error)
    return null
  }
}

/**
 * Regenerate a single product
 */
export async function regenerateSingle(
  productGroupId: string
): Promise<RegenerationJobResponse | { error: string }> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { error: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${API_URL}/api/regeneration/regenerate-single`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_group_id: productGroupId }),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to regenerate' }))
      return { error: errorData.detail || errorData.message }
    }

    return await response.json()
  } catch (error) {
    console.error('Error regenerating:', error)
    return { error: 'Network error' }
  }
}

/**
 * Regenerate all rejected products for a client
 */
export async function regenerateRejected(
  clientId: string
): Promise<RegenerationJobResponse | { error: string }> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { error: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${API_URL}/api/regeneration/${clientId}/regenerate-rejected`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to regenerate' }))
      return { error: errorData.detail || errorData.message }
    }

    return await response.json()
  } catch (error) {
    console.error('Error regenerating:', error)
    return { error: 'Network error' }
  }
}
