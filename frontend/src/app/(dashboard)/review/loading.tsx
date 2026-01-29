import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'

export default function ReviewLoading() {
  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <Skeleton className="h-10 w-full" />

      {/* Main review area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Content area */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardContent className="p-6">
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar action buttons */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
