'use client'

import { useDebug } from '@/lib/debug-context'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

export function DebugToggle() {
  const { isDebugEnabled, setDebugEnabled, isAdmin } = useDebug()

  if (!isAdmin) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Switch
          id="debug-mode"
          checked={isDebugEnabled}
          onCheckedChange={setDebugEnabled}
        />
        <Label htmlFor="debug-mode" className="text-sm font-medium">
          Enable Debug Mode
        </Label>
      </div>
      <p className="text-sm text-muted-foreground">
        When enabled, shows exact AI prompts, model parameters, and costs in a
        panel at the bottom of every page. Debug mode is active until you close
        this browser tab.
      </p>
    </div>
  )
}
