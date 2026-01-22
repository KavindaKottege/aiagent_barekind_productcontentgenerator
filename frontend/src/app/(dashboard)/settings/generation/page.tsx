import { redirect } from "next/navigation";
import { getAdmin } from "@/lib/dal";
import { getGenerationSettings } from "@/app/actions/settings";
import { GenerationSettingsForm } from "@/components/forms/generation-settings-form";

export default async function GenerationSettingsPage() {
  // Admin only
  const user = await getAdmin();
  if (!user) {
    redirect("/dashboard?error=admin_required");
  }

  const settings = await getGenerationSettings();

  if (!settings) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
        Failed to load generation settings
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Generation Settings</h1>
        <p className="text-gray-600">
          Configure AI model behavior and cost controls.
        </p>
      </div>

      <GenerationSettingsForm initialSettings={settings} />

      {/* Cost summary card */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded">
        <h3 className="font-semibold text-blue-800 mb-2">Cost Estimation</h3>
        <p className="text-sm text-blue-700">
          GPT-5.2 costs approximately $0.02-$0.03 per product (title +
          description). A batch of 1,000 products typically costs $20-$30. The
          soft cap helps prevent unexpected charges during large batches.
        </p>
      </div>
    </div>
  );
}
