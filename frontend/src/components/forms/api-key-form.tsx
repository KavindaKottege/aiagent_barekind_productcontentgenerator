"use client";

import { useActionState } from "react";
import { updateSettings, type FormState } from "@/app/actions/settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ApiKeyFormProps {
  currentKey: string | null;
}

export function ApiKeyForm({ currentKey }: ApiKeyFormProps) {
  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    updateSettings,
    {}
  );

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <Label htmlFor="openai_api_key">OpenAI API Key</Label>
        <Input
          id="openai_api_key"
          name="openai_api_key"
          type="text"
          defaultValue={currentKey || ""}
          placeholder="sk-..."
          disabled={isPending}
          error={state?.errors?.openai_api_key?.[0]}
        />
        <p className="mt-1 text-sm text-gray-500">
          This API key is used for all content generation. Get your key from{" "}
          <a
            href="https://platform.openai.com/api-keys"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            OpenAI Platform
          </a>
          .
        </p>
      </div>

      {state?.errors?._form && (
        <div className="text-sm text-red-600">{state.errors._form[0]}</div>
      )}

      {state?.success && (
        <div className="text-sm text-green-600">
          API key saved successfully!
        </div>
      )}

      <Button type="submit" disabled={isPending}>
        {isPending ? "Saving..." : "Save API Key"}
      </Button>
    </form>
  );
}
