'use server'

import { revalidatePath } from 'next/cache'
import { getAccessToken } from '@/lib/session'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface GenerationJob {
  id: string
  client_id: string
  user_id: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  status_reason: string | null
  total_count: number
  completed_count: number
  success_count: number
  failed_count: number
  total_cost: string
  total_input_tokens: number
  total_output_tokens: number
  started_at: string | null
  completed_at: string | null
  paused_at: string | null
  created_at: string
  updated_at: string
}

export interface GenerationProgress {
  status: string
  completed: number
  total: number
  success: number
  failed: number
  cost: string
  projected_cost: string
  elapsed_seconds: number
  estimated_remaining_seconds: number | null
  status_reason?: string
}

export interface GenerationCompleteSummary {
  status: string
  summary: {
    total_products: number
    successful: number
    failed: number
    total_cost: string
    elapsed_seconds: number
  }
}

export interface SoftCapInfo {
  current_cost: string
  projected_cost: string
  soft_cap: string
  completed: number
  total: number
  message: string
}

export async function startGeneration(clientId: string): Promise<{
  success: boolean
  job?: GenerationJob
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ client_id: clientId }),
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to start generation' }
    }

    const job = await response.json()
    revalidatePath('/products')
    return { success: true, job }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function getJobStatus(jobId: string): Promise<{
  success: boolean
  job?: GenerationJob
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/jobs/${jobId}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to get job status' }
    }

    const job = await response.json()
    return { success: true, job }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function getActiveJobForClient(clientId: string): Promise<{
  success: boolean
  job?: GenerationJob | null
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/client/${clientId}/active`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to get active job' }
    }

    // Response is null if no active job
    const text = await response.text()
    const job = text ? JSON.parse(text) : null
    return { success: true, job }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function pauseGeneration(jobId: string): Promise<{
  success: boolean
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/jobs/${jobId}/pause`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to pause generation' }
    }

    return { success: true }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function cancelGeneration(jobId: string): Promise<{
  success: boolean
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/jobs/${jobId}/cancel`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to cancel generation' }
    }

    revalidatePath('/products')
    return { success: true }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function resumeGeneration(jobId: string): Promise<{
  success: boolean
  job?: GenerationJob
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${API_URL}/api/generation/jobs/${jobId}/resume`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to resume generation' }
    }

    const job = await response.json()
    return { success: true, job }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}

export async function softCapContinue(jobId: string, continueGeneration: boolean): Promise<{
  success: boolean
  job?: GenerationJob | null
  error?: string
}> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${API_URL}/api/generation/jobs/${jobId}/soft-cap-continue?continue_generation=${continueGeneration}`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to process soft cap response' }
    }

    const text = await response.text()
    const job = text ? JSON.parse(text) : null
    return { success: true, job }
  } catch (error) {
    return { success: false, error: 'Network error' }
  }
}
