'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

interface ReviewAction {
  productId: string
  action: 'approve' | 'reject' | 'edit'
  previousStatus: string | null
  previousEditedTitle?: string | null
  previousEditedDescription?: string | null
  timestamp: Date
}

interface ReviewHistory {
  past: ReviewAction[]
  future: ReviewAction[]
}

interface ReviewContextValue {
  recordAction: (action: Omit<ReviewAction, 'timestamp'>) => void
  undo: () => ReviewAction | null
  redo: () => ReviewAction | null
  canUndo: boolean
  canRedo: boolean
  clearHistory: () => void
}

const ReviewContext = createContext<ReviewContextValue | null>(null)

export function ReviewProvider({ children }: { children: ReactNode }) {
  const [history, setHistory] = useState<ReviewHistory>({
    past: [],
    future: []
  })

  const recordAction = useCallback((action: Omit<ReviewAction, 'timestamp'>) => {
    const fullAction: ReviewAction = { ...action, timestamp: new Date() }
    setHistory(prev => ({
      past: [...prev.past, fullAction],
      future: [] // Clear redo stack on new action
    }))
  }, [])

  const undo = useCallback(() => {
    if (history.past.length === 0) return null

    const lastAction = history.past[history.past.length - 1]
    setHistory(prev => ({
      past: prev.past.slice(0, -1),
      future: [lastAction, ...prev.future]
    }))

    return lastAction
  }, [history.past])

  const redo = useCallback(() => {
    if (history.future.length === 0) return null

    const nextAction = history.future[0]
    setHistory(prev => ({
      past: [...prev.past, nextAction],
      future: prev.future.slice(1)
    }))

    return nextAction
  }, [history.future])

  const clearHistory = useCallback(() => {
    setHistory({ past: [], future: [] })
  }, [])

  return (
    <ReviewContext.Provider value={{
      recordAction,
      undo,
      redo,
      canUndo: history.past.length > 0,
      canRedo: history.future.length > 0,
      clearHistory
    }}>
      {children}
    </ReviewContext.Provider>
  )
}

export function useReviewHistory() {
  const context = useContext(ReviewContext)
  if (!context) {
    throw new Error('useReviewHistory must be used within ReviewProvider')
  }
  return context
}
