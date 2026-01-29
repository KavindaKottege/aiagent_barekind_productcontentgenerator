'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
      <h2 className="text-xl font-semibold text-gray-900">
        Something went wrong
      </h2>
      <p className="text-gray-600 max-w-md text-center">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <div className="flex items-center gap-3 pt-2">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard">Go to Dashboard</Link>
        </Button>
      </div>
    </div>
  )
}
