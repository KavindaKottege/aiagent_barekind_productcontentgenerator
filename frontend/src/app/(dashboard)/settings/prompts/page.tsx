import { getAdmin } from '@/lib/dal'
import { getPromptSettings } from '@/app/actions/settings'
import { PromptSettingsForm } from '@/components/forms/prompt-settings-form'

export default async function PromptSettingsPage() {
  // Verify admin access - redirects non-admins
  await getAdmin()

  const settings = await getPromptSettings()

  if (!settings) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="p-4 bg-red-50 text-red-600 rounded-md">
          Failed to load prompt settings. Please try again.
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <PromptSettingsForm initialSettings={settings} />
    </div>
  )
}
