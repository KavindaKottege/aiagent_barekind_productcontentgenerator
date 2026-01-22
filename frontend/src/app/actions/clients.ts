'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { getAccessToken } from '@/lib/session'
import { clientSchema } from '@/lib/schemas'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Client {
  id: string
  user_id: string
  brand_name: string
  story: string | null
  tone: string | null
  language: string | null
  guidelines: string | null
  system_prompt: string | null
  task1_prompt: string | null
  task2_prompt: string | null
  has_custom_prompts: boolean
  created_at: string
  updated_at: string
}

export interface ClientActionState {
  errors?: {
    brand_name?: string[]
    _form?: string[]
  }
  success?: boolean
}

export async function getClients(): Promise<Client[]> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  const response = await fetch(`${API_URL}/clients/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: 'no-store',
  })

  if (!response.ok) {
    if (response.status === 401) redirect('/login')
    throw new Error('Failed to fetch clients')
  }

  return response.json()
}

export async function getClient(id: string): Promise<Client | null> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  const response = await fetch(`${API_URL}/clients/${id}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: 'no-store',
  })

  if (!response.ok) {
    if (response.status === 401) redirect('/login')
    if (response.status === 404) return null
    throw new Error('Failed to fetch client')
  }

  return response.json()
}

export async function createClient(
  prevState: ClientActionState,
  formData: FormData
): Promise<ClientActionState> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  // Parse and validate
  const rawData = {
    brand_name: formData.get('brand_name') as string,
    story: formData.get('story') as string || null,
    tone: formData.get('tone') as string || null,
    language: formData.get('language') as string || null,
    guidelines: formData.get('guidelines') as string || null,
    system_prompt: formData.get('system_prompt') as string || null,
    task1_prompt: formData.get('task1_prompt') as string || null,
    task2_prompt: formData.get('task2_prompt') as string || null,
  }

  const validatedFields = clientSchema.safeParse(rawData)
  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors }
  }

  // Create client
  const response = await fetch(`${API_URL}/clients/`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(validatedFields.data),
  })

  if (!response.ok) {
    if (response.status === 401) redirect('/login')
    const error = await response.json()
    return { errors: { _form: [error.detail || 'Failed to create client'] } }
  }

  revalidatePath('/clients')
  redirect('/clients')
}

export async function updateClient(
  clientId: string,
  prevState: ClientActionState,
  formData: FormData
): Promise<ClientActionState> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  // Parse and validate
  const rawData = {
    brand_name: formData.get('brand_name') as string,
    story: formData.get('story') as string || null,
    tone: formData.get('tone') as string || null,
    language: formData.get('language') as string || null,
    guidelines: formData.get('guidelines') as string || null,
    system_prompt: formData.get('system_prompt') as string || null,
    task1_prompt: formData.get('task1_prompt') as string || null,
    task2_prompt: formData.get('task2_prompt') as string || null,
  }

  const validatedFields = clientSchema.safeParse(rawData)
  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors }
  }

  // Update client
  const response = await fetch(`${API_URL}/clients/${clientId}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(validatedFields.data),
  })

  if (!response.ok) {
    if (response.status === 401) redirect('/login')
    if (response.status === 404) return { errors: { _form: ['Client not found'] } }
    const error = await response.json()
    return { errors: { _form: [error.detail || 'Failed to update client'] } }
  }

  revalidatePath('/clients')
  revalidatePath(`/clients/${clientId}`)
  redirect('/clients')
}

export async function deleteClient(clientId: string): Promise<{ success: boolean; error?: string }> {
  const accessToken = await getAccessToken()
  if (!accessToken) {
    redirect('/login')
  }

  const response = await fetch(`${API_URL}/clients/${clientId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (!response.ok) {
    if (response.status === 401) redirect('/login')
    if (response.status === 403) return { success: false, error: 'Admin access required' }
    if (response.status === 404) return { success: false, error: 'Client not found' }
    return { success: false, error: 'Failed to delete client' }
  }

  revalidatePath('/clients')
  return { success: true }
}
