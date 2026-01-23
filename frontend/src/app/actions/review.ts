'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

// Types matching backend Pydantic schemas
export interface ProductGroupReview {
  id: string
  product_name: string
  product_token: string
  sku: string
  variant_count: number
  generated_title: string | null
  generated_description: string | null
  edited_title: string | null
  edited_description: string | null
  status: string
  review_status: string | null
  ai_review_status: string | null
  ai_review_reason: string | null
  ai_review_safety_flags: string[]
  images: string[]
  original_data: Record<string, unknown>
  row_index: number
  reviewed_at: string | null
  ai_reviewed_at: string | null
}

export interface ReviewStats {
  total_generated: number
  pending_review: number
  manually_approved: number
  manually_rejected: number
  ai_approved: number
  ai_rejected: number
  edited: number
}

export interface ReviewActionResult {
  success: boolean
  message?: string
  next_product_id?: string
}

async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies()
  return cookieStore.get('access_token')?.value || null
}

/**
 * Fetch products for review UI with optional status filter
 */
export async function getReviewProducts(
  clientId: string,
  statusFilter?: string
): Promise<ProductGroupReview[]> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    redirect('/login')
  }

  try {
    const url = new URL(`${process.env.BACKEND_URL}/api/review/${clientId}/products`)
    if (statusFilter && statusFilter !== 'all') {
      url.searchParams.set('status', statusFilter)
    }

    const response = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/login')
      }
      console.error(`Failed to fetch review products: ${response.status}`)
      return []
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching review products:', error)
    return []
  }
}

/**
 * Fetch single product for review detail
 */
export async function getReviewProduct(
  clientId: string,
  productGroupId: string
): Promise<ProductGroupReview | null> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/product/${productGroupId}`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/login')
      }
      console.error(`Failed to fetch review product: ${response.status}`)
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching review product:', error)
    return null
  }
}

/**
 * Approve product and get next unreviewed product ID
 */
export async function approveProduct(
  productGroupId: string
): Promise<ReviewActionResult> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false, message: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL}/api/review/approve`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_group_id: productGroupId,
        action: 'approve',
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to approve' }))
      return {
        success: false,
        message: errorData.message || `Approve failed: ${response.status}`,
      }
    }

    const data = await response.json()
    return {
      success: true,
      message: data.message || 'Product approved',
      next_product_id: data.next_product_id,
    }
  } catch (error) {
    console.error('Error approving product:', error)
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Reject product and get next unreviewed product ID
 */
export async function rejectProduct(
  productGroupId: string
): Promise<ReviewActionResult> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false, message: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL}/api/review/reject`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_group_id: productGroupId,
        action: 'reject',
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to reject' }))
      return {
        success: false,
        message: errorData.message || `Reject failed: ${response.status}`,
      }
    }

    const data = await response.json()
    return {
      success: true,
      message: data.message || 'Product rejected',
      next_product_id: data.next_product_id,
    }
  } catch (error) {
    console.error('Error rejecting product:', error)
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Save edited title and description with client-side validation
 */
export async function saveEdit(
  productGroupId: string,
  title: string,
  description: string
): Promise<ReviewActionResult> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false, message: 'Not authenticated' }
  }

  // Client-side validation for character limits
  if (title.length < 30 || title.length > 60) {
    return {
      success: false,
      message: `Title must be 30-60 characters (currently ${title.length})`,
    }
  }

  if (description.length < 2000 || description.length > 3000) {
    return {
      success: false,
      message: `Description must be 2000-3000 characters (currently ${description.length})`,
    }
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL}/api/review/edit`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_group_id: productGroupId,
        edited_title: title,
        edited_description: description,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to save edit' }))
      return {
        success: false,
        message: errorData.message || `Save failed: ${response.status}`,
      }
    }

    const data = await response.json()
    return {
      success: true,
      message: data.message || 'Edit saved successfully',
    }
  } catch (error) {
    console.error('Error saving edit:', error)
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Undo review action by reverting to previous status
 */
export async function undoReview(
  productGroupId: string,
  previousStatus: string | null
): Promise<ReviewActionResult> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false, message: 'Not authenticated' }
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL}/api/review/undo`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_group_id: productGroupId,
        previous_status: previousStatus,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to undo' }))
      return {
        success: false,
        message: errorData.message || `Undo failed: ${response.status}`,
      }
    }

    const data = await response.json()
    return {
      success: true,
      message: data.message || 'Action undone',
    }
  } catch (error) {
    console.error('Error undoing review:', error)
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Get review statistics for client
 */
export async function getReviewStats(clientId: string): Promise<ReviewStats> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/stats`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/login')
      }
      console.error(`Failed to fetch review stats: ${response.status}`)
      return {
        total_generated: 0,
        pending_review: 0,
        manually_approved: 0,
        manually_rejected: 0,
        ai_approved: 0,
        ai_rejected: 0,
        edited: 0,
      }
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching review stats:', error)
    return {
      total_generated: 0,
      pending_review: 0,
      manually_approved: 0,
      manually_rejected: 0,
      ai_approved: 0,
      ai_rejected: 0,
      edited: 0,
    }
  }
}

/**
 * Get next unreviewed product ID for auto-advance
 */
export async function getNextUnreviewed(clientId: string): Promise<string | null> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/next-unreviewed`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/login')
      }
      console.error(`Failed to fetch next unreviewed: ${response.status}`)
      return null
    }

    const data = await response.json()
    return data.next_product_id || null
  } catch (error) {
    console.error('Error fetching next unreviewed:', error)
    return null
  }
}

// AI Review Types
export interface AIReviewResult {
  recommendation: 'approve' | 'reject'
  reason: string
  safety_flags: string[]
  accuracy_score: number
}

export interface AIReviewJobStatus {
  status: string
  total_count: number
  completed_count: number
  total_cost: string
  auto_approve: boolean  // Whether in AI-auto mode
  estimated_remaining: number | null
}

/**
 * Request AI review for single product (AI-assisted mode)
 */
export async function requestAIReview(
  productGroupId: string
): Promise<AIReviewResult | null> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return null
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/ai-single`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_group_id: productGroupId,
        }),
      }
    )

    if (!response.ok) {
      console.error(`Failed to request AI review: ${response.status}`)
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error requesting AI review:', error)
    return null
  }
}

/**
 * Start batch AI review job
 */
export async function startBatchAIReview(
  clientId: string,
  autoApprove: boolean = false
): Promise<{ jobId: string } | { error: string }> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { error: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/ai-review/start`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          auto_approve: autoApprove,
        }),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to start AI review' }))
      return { error: errorData.message || `Start failed: ${response.status}` }
    }

    const data = await response.json()
    return { jobId: data.job_id }
  } catch (error) {
    console.error('Error starting batch AI review:', error)
    return { error: error instanceof Error ? error.message : 'Network error' }
  }
}

/**
 * Get batch AI review status
 */
export async function getBatchAIReviewStatus(
  clientId: string
): Promise<AIReviewJobStatus | null> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return null
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/ai-review/status`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      console.error(`Failed to fetch AI review status: ${response.status}`)
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching AI review status:', error)
    return null
  }
}

/**
 * Pause batch AI review job
 */
export async function pauseBatchAIReview(
  clientId: string
): Promise<{ success: boolean }> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false }
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/ai-review/pause`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )

    return { success: response.ok }
  } catch (error) {
    console.error('Error pausing AI review:', error)
    return { success: false }
  }
}

/**
 * Cancel batch AI review job
 */
export async function cancelBatchAIReview(
  clientId: string
): Promise<{ success: boolean }> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { success: false }
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/ai-review/cancel`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    )

    return { success: response.ok }
  } catch (error) {
    console.error('Error cancelling AI review:', error)
    return { success: false }
  }
}

/**
 * Resume batch AI review job
 */
export async function resumeBatchAIReview(
  clientId: string,
  autoApprove: boolean = false
): Promise<{ jobId: string } | { error: string }> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    return { error: 'Not authenticated' }
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/review/${clientId}/ai-review/resume`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          auto_approve: autoApprove,
        }),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to resume AI review' }))
      return { error: errorData.message || `Resume failed: ${response.status}` }
    }

    const data = await response.json()
    return { jobId: data.job_id }
  } catch (error) {
    console.error('Error resuming AI review:', error)
    return { error: error instanceof Error ? error.message : 'Network error' }
  }
}
