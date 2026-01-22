'use client'

import { ClientProvider } from '@/lib/client-context'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ClientProvider>
      {children}
    </ClientProvider>
  )
}
