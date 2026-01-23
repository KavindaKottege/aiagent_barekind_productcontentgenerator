import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

/**
 * API route for client-side fetching of review products and stats
 * Used for real-time updates during generation
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const clientId = searchParams.get('clientId')
  const statusFilter = searchParams.get('status') || 'all'

  if (!clientId) {
    return NextResponse.json({ error: 'Missing clientId' }, { status: 400 })
  }

  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  if (!accessToken) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    // Fetch products and stats in parallel
    const [productsRes, statsRes] = await Promise.all([
      fetch(
        `${backendUrl}/api/review/${clientId}/products${statusFilter !== 'all' ? `?status=${statusFilter}` : ''}`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          cache: 'no-store',
        }
      ),
      fetch(`${backendUrl}/api/review/${clientId}/stats`, {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: 'no-store',
      }),
    ])

    if (!productsRes.ok || !statsRes.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch review data' },
        { status: productsRes.status || statsRes.status }
      )
    }

    const [products, stats] = await Promise.all([
      productsRes.json(),
      statsRes.json(),
    ])

    return NextResponse.json({ products, stats })
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
