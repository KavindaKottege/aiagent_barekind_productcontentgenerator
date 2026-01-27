import { getAdmin } from '@/lib/dal'
import { getTaskSettings, updateTaskSettings } from '@/app/actions/settings'
import { AiTaskSettingsForm } from '@/components/forms/ai-task-settings-form'

export default async function TaskSettingsPage() {
  // Verify admin access - redirects non-admins
  await getAdmin()

  const settings = await getTaskSettings()

  if (!settings) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="p-4 bg-red-50 text-red-600 rounded-md">
          Failed to load task settings. Please try again.
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <AiTaskSettingsForm
        initialSettings={settings}
        onSave={updateTaskSettings}
      />
    </div>
  )
}
