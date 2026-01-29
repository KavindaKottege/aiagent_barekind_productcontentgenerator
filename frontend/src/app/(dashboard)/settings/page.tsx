import Link from "next/link";
import { getAdmin, getUser } from "@/lib/dal";
import { getSettings } from "@/app/actions/settings";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ApiKeyForm } from "@/components/forms/api-key-form";
import { DebugToggle } from "@/components/debug-toggle";

export default async function SettingsPage() {
  // Verify user is admin (redirects if not)
  await getAdmin();

  // Fetch current settings and user
  const settings = await getSettings();
  const user = await getUser();

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>OpenAI API Key</CardTitle>
            <CardDescription>
              Configure your OpenAI API key for content generation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ApiKeyForm currentKey={settings?.openai_api_key || null} />
          </CardContent>
        </Card>

        {user.is_admin && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>AI Task Settings</CardTitle>
                <CardDescription>
                  Configure AI prompts, input attributes, and length constraints for generation and review tasks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/settings/prompts">
                  <Button variant="outline">Manage AI Tasks</Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Generation Settings</CardTitle>
                <CardDescription>
                  Configure AI model behavior and cost controls
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/settings/generation">
                  <Button variant="outline">Manage Generation Settings</Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Debug Mode</CardTitle>
                <CardDescription>
                  View exact AI prompts and model parameters during content generation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DebugToggle />
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
