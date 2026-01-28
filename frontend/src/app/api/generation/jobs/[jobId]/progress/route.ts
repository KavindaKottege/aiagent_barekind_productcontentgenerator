import { NextRequest } from 'next/server'
import { cookies } from 'next/headers'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Disable static optimization for this route
export const dynamic = 'force-dynamic'

/**
 * Proxy SSE endpoint for generation progress.
 * This avoids CORS issues by making the SSE connection same-origin.
 */
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ jobId: string }> }
) {
  // Get params
  const { jobId } = await context.params

  // Get access token from cookie
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value

  console.log('[SSE Proxy] Request for job:', jobId, 'has token:', !!accessToken)

  if (!accessToken) {
    console.error('[SSE Proxy] No access token')
    return new Response('Unauthorized', { status: 401 })
  }

  // Create upstream SSE URL
  const upstreamUrl = `${API_URL}/api/generation/jobs/${jobId}/progress?token=${encodeURIComponent(accessToken)}`

  console.log('[SSE Proxy] Fetching from backend...')

  try {
    // Fetch from backend with SSE
    const response = await fetch(upstreamUrl, {
      headers: {
        Accept: 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      // Important: don't timeout
      signal: AbortSignal.timeout(300000), // 5 minutes
    })

    console.log('[SSE Proxy] Backend response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('[SSE Proxy] Backend error:', response.status, errorText)
      return new Response(errorText, { status: response.status })
    }

    // Check if we got a streaming response
    if (!response.body) {
      console.error('[SSE Proxy] No response body')
      return new Response('No response body', { status: 500 })
    }

    console.log('[SSE Proxy] Streaming response to client...')

    // Pass through the response body directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'X-Accel-Buffering': 'no',
      },
    })
  } catch (error) {
    console.error('[SSE Proxy] Connection error:', error)
    return new Response(`Failed to connect to backend: ${error}`, { status: 502 })
  }
}
