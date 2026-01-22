'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'

export type UploadResult = {
  success: boolean
  error?: string
  data?: {
    total_rows: number
    product_groups: number
    variant_groups: number
    standalone_products: number
    mapped_columns: Record<string, string>
    unmapped_columns: string[]
    mapping_confidence: string
  }
}

export async function uploadProducts(formData: FormData): Promise<UploadResult> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return { success: false, error: 'Not authenticated' }
  }

  const file = formData.get('file') as File | null
  const clientId = formData.get('clientId') as string | null

  if (!file || file.size === 0) {
    return { success: false, error: 'Please select a file to upload' }
  }

  if (!clientId) {
    return { success: false, error: 'Please select a client first' }
  }

  // Validate file type
  const validExtensions = ['.xlsx', '.xls']
  const hasValidExtension = validExtensions.some(ext =>
    file.name.toLowerCase().endsWith(ext)
  )
  if (!hasValidExtension) {
    return { success: false, error: 'Only Excel files (.xlsx, .xls) are supported' }
  }

  // Forward to FastAPI backend
  const backendFormData = new FormData()
  backendFormData.append('file', file)

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/products/upload?client_id=${clientId}`,
      {
        method: 'POST',
        body: backendFormData,
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
      return {
        success: false,
        error: errorData.detail || `Upload failed: ${response.status}`,
      }
    }

    const data = await response.json()

    // Revalidate products page cache
    revalidatePath('/products')

    return { success: true, data }
  } catch (error) {
    console.error('Upload error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error during upload',
    }
  }
}

export type ProductGroup = {
  id: string
  product_name: string
  product_token: string
  sku: string
  variant_count: number
  status: string
  generated_title: string | null
  generated_description: string | null
  created_at: string
}

export async function getProductGroups(clientId: string): Promise<ProductGroup[]> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    redirect('/login')
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/products/groups?client_id=${clientId}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        cache: 'no-store',
      }
    )

    if (!response.ok) {
      if (response.status === 401) {
        redirect('/login')
      }
      return []
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching product groups:', error)
    return []
  }
}
