import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ groupId: string }> }
) {
  const { groupId } = await params
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const url = `${apiUrl}/api/products/groups/${groupId}`

    console.log('[API Route] Fetching variants from:', url)

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    console.log('[API Route] Response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('[API Route] Error response:', errorText)
      return NextResponse.json(
        { error: 'Failed to fetch', details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('[API Route] Success, variants count:', data.variants?.length || 0)
    return NextResponse.json(data)
  } catch (error) {
    console.error('[API Route] Exception:', error)
    return NextResponse.json(
      { error: 'Internal error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
