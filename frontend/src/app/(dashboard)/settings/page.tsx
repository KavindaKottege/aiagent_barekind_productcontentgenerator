import { getAdmin } from "@/lib/dal";
import { getSettings } from "@/app/actions/settings";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ApiKeyForm } from "@/components/forms/api-key-form";

export default async function SettingsPage() {
  // Verify user is admin (redirects if not)
  await getAdmin();

  // Fetch current settings
  const settings = await getSettings();

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">OpenAI API Key</h2>
          <p className="text-sm text-gray-600">
            Configure your OpenAI API key for content generation
          </p>
        </CardHeader>
        <CardContent>
          <ApiKeyForm currentKey={settings?.openai_api_key || null} />
        </CardContent>
      </Card>
    </div>
  );
}
