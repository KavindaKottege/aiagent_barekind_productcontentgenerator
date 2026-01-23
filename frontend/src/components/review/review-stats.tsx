'use client'

import { Badge } from '@/components/ui/badge'
import { ReviewStats } from '@/app/actions/review'

interface ReviewStatsProps {
  stats: ReviewStats
  onFilterClick?: (status: string) => void
}

export function ReviewStatsComponent({ stats, onFilterClick }: ReviewStatsProps) {
  const badges = [
    { label: 'Pending Review', count: stats.pending_review, color: 'bg-gray-100 text-gray-700 hover:bg-gray-200', status: 'pending' },
    { label: 'Approved', count: stats.manually_approved, color: 'bg-green-100 text-green-700 hover:bg-green-200', status: 'approved' },
    { label: 'Rejected', count: stats.manually_rejected, color: 'bg-red-100 text-red-700 hover:bg-red-200', status: 'rejected' },
    { label: 'AI Approved', count: stats.ai_approved, color: 'bg-blue-100 text-blue-700 hover:bg-blue-200', status: 'ai_approved' },
    { label: 'AI Rejected', count: stats.ai_rejected, color: 'bg-orange-100 text-orange-700 hover:bg-orange-200', status: 'ai_rejected' },
    { label: 'Edited', count: stats.edited, color: 'bg-purple-100 text-purple-700 hover:bg-purple-200', status: 'edited' },
  ]

  return (
    <div className="flex flex-wrap gap-2 items-center py-3">
      <span className="text-sm font-medium text-gray-700 mr-2">
        Review Status:
      </span>
      {badges.map(({ label, count, color, status }) => (
        <button
          key={status}
          onClick={() => onFilterClick?.(status)}
          className={`${color} px-3 py-1 rounded-full text-sm font-medium transition-colors cursor-pointer`}
        >
          {label}: {count}
        </button>
      ))}
      <span className="text-sm text-gray-500 ml-2">
        Total Generated: {stats.total_generated}
      </span>
    </div>
  )
}
