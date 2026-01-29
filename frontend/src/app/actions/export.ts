'use server'

import { cookies } from 'next/headers'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ExportStats {
  total: number
  not_generated: number
  approved: number
  pending: number
  rejected: number
}

/**
 * Fetch export statistics for the confirmation dialog.
 * Returns product counts by status for the selected client.
 */
export async function getExportStats(clientId: string): Promise<ExportStats | null> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return null
  }

  try {
    const response = await fetch(
      `${API_URL}/api/export/${clientId}/stats`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      console.error(`Failed to fetch export stats: ${response.status}`)
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching export stats:', error)
    return null
  }
}

/**
 * Get the access token for client-side fetch to FastAPI.
 * This is the token passing pattern used by SSE in the review page.
 * The client component needs this to make a direct fetch to FastAPI for the binary download.
 */
export async function getExportToken(): Promise<string | undefined> {
  const cookieStore = await cookies()
  return cookieStore.get('access_token')?.value
}
