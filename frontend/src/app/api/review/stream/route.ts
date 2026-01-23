import { NextRequest } from 'next/server'

/**
 * SSE proxy for review page to listen to generation progress
 * This allows the review page to update in real-time as new products are generated
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const clientId = searchParams.get('clientId')
  const token = searchParams.get('token')

  if (!clientId || !token) {
    return new Response('Missing clientId or token', { status: 400 })
  }

  try {
    // Connect to backend SSE endpoint for generation progress
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const sseUrl = `${backendUrl}/api/generation/client/${clientId}/progress?token=${token}`

    const response = await fetch(sseUrl, {
      headers: {
        Accept: 'text/event-stream',
      },
    })

    if (!response.ok) {
      return new Response(`Backend SSE connection failed: ${response.status}`, {
        status: response.status,
      })
    }

    // Forward the SSE stream from backend to frontend client
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable nginx buffering
      },
    })
  } catch (error) {
    console.error('SSE proxy error:', error)
    return new Response('SSE proxy error', { status: 500 })
  }
}
