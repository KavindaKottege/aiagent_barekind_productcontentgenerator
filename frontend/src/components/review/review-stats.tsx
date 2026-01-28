'use client'

import { Badge } from '@/components/ui/badge'
import { ReviewStats } from '@/app/actions/review'

interface ReviewStatsProps {
  stats: ReviewStats
  activeFilter?: string
  onFilterClick?: (status: string) => void
}

// Export badge styles so they can be reused in product cards
export const statusBadgeStyles = {
  pending: 'bg-gray-100 text-gray-700',
  approved: 'bg-brand-green-light text-brand-green-hover',
  rejected: 'bg-red-100 text-red-700',
  ai_approved: 'bg-brand-blue-light text-brand-blue',
  ai_rejected: 'bg-orange-100 text-orange-700',
  edited: 'bg-purple-100 text-purple-700',
  all: 'bg-gray-100 text-gray-700',
}

export function ReviewStatsComponent({ stats, activeFilter = 'all', onFilterClick }: ReviewStatsProps) {
  const badges = [
    { label: 'All', count: stats.total_generated, status: 'all' },
    { label: 'Pending Review', count: stats.pending_review, status: 'pending' },
    { label: 'Approved', count: stats.manually_approved, status: 'approved' },
    { label: 'Rejected', count: stats.manually_rejected, status: 'rejected' },
    { label: 'AI Approved', count: stats.ai_approved, status: 'ai_approved' },
    { label: 'AI Rejected', count: stats.ai_rejected, status: 'ai_rejected' },
    { label: 'Edited', count: stats.edited, status: 'edited' },
  ]

  return (
    <div className="flex flex-wrap gap-2 items-center py-3">
      <span className="text-sm font-medium text-gray-700 mr-2">
        Review Status:
      </span>
      {badges.map(({ label, count, status }) => {
        const isActive = activeFilter === status
        const baseColor = statusBadgeStyles[status as keyof typeof statusBadgeStyles]
        return (
          <button
            key={status}
            onClick={() => onFilterClick?.(status)}
            className={`${baseColor} px-3 py-1 rounded-full text-sm font-medium transition-colors cursor-pointer ${
              isActive ? 'ring-2 ring-offset-1 ring-brand-blue' : 'hover:opacity-80'
            }`}
          >
            {label}: {count}
          </button>
        )
      })}
    </div>
  )
}
