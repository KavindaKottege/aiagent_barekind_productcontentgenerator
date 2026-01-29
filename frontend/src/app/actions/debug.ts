'use server'

import { cookies } from 'next/headers'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface DebugLogEntry {
  id: string
  job_id: string
  product_group_id: string
  attempt_number: number
  prompt_used: string
  model_version: string
  temperature: number
  input_tokens: number
  output_tokens: number
  cost: string
  duration_ms: number
  success: boolean
  error_message: string | null
  generated_title: string | null
  generated_description: string | null
  title_length: number | null
  description_length: number | null
  created_at: string
}

/**
 * Fetch debug audit logs for a specific generation job.
 * Admin-only -- returns empty array for non-admin users (403 silently handled).
 */
export async function getDebugLogs(
  jobId: string,
  since?: string,
): Promise<DebugLogEntry[]> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return []
  }

  try {
    let url = `${API_URL}/api/debug/logs/${jobId}`
    if (since) {
      url += `?since=${encodeURIComponent(since)}`
    }

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      return []
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching debug logs:', error)
    return []
  }
}

/**
 * Fetch debug audit logs for the most recent job of a client.
 * Useful when the debug panel opens mid-generation and the job_id is unknown.
 * Admin-only -- returns empty array for non-admin users.
 */
export async function getDebugLogsForClient(
  clientId: string,
  since?: string,
): Promise<DebugLogEntry[]> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return []
  }

  try {
    let url = `${API_URL}/api/debug/logs/client/${clientId}/latest`
    if (since) {
      url += `?since=${encodeURIComponent(since)}`
    }

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      return []
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching debug logs for client:', error)
    return []
  }
}

/**
 * Get the access token for client-side polling of debug logs.
 * Returns undefined if no session cookie is present.
 */
export async function getDebugToken(): Promise<string | undefined> {
  const cookieStore = await cookies()
  return cookieStore.get('access_token')?.value
}
