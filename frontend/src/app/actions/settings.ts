"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getAccessToken } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Settings {
  openai_api_key: string | null;
  has_api_key: boolean;
  ai_model: string;
  ai_temperature: string;
  generation_soft_cap: string;
}

export interface FormState {
  errors?: {
    openai_api_key?: string[];
    _form?: string[];
  };
  success?: boolean;
}

export interface PromptSettings {
  default_system_prompt: string | null;
  default_task1_prompt: string | null;
  default_task2_prompt: string | null;
}

export interface PromptSettingsActionState {
  errors?: {
    _form?: string[];
  };
  success?: boolean;
}

export interface GenerationSettings {
  ai_model: string;
  ai_temperature: string;
  generation_soft_cap: string;
}

export async function getSettings(): Promise<Settings | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  const response = await fetch(`${API_URL}/api/settings/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    return null;
  }

  return response.json();
}

export async function updateSettings(
  prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const openai_api_key = formData.get("openai_api_key") as string;

  // Validation
  if (!openai_api_key || openai_api_key.trim() === "") {
    return {
      errors: {
        openai_api_key: ["API key is required"],
      },
    };
  }

  if (!openai_api_key.startsWith("sk-")) {
    return {
      errors: {
        openai_api_key: ["API key must start with 'sk-'"],
      },
    };
  }

  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  const response = await fetch(`${API_URL}/api/settings/`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ openai_api_key }),
  });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    const error = await response.json();
    return {
      errors: {
        _form: [error.detail || "Failed to update settings"],
      },
    };
  }

  // Revalidate the settings page to show updated value
  revalidatePath("/settings");

  return {
    success: true,
  };
}

export async function getPromptSettings(): Promise<PromptSettings | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  const response = await fetch(`${API_URL}/api/settings/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    if (response.status === 403) redirect("/dashboard?error=admin_required");
    return null;
  }

  const data = await response.json();
  return {
    default_system_prompt: data.default_system_prompt,
    default_task1_prompt: data.default_task1_prompt,
    default_task2_prompt: data.default_task2_prompt,
  };
}

export async function updatePromptSettings(
  prevState: PromptSettingsActionState,
  formData: FormData
): Promise<PromptSettingsActionState> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  const payload = {
    default_system_prompt: formData.get("default_system_prompt") as string || null,
    default_task1_prompt: formData.get("default_task1_prompt") as string || null,
    default_task2_prompt: formData.get("default_task2_prompt") as string || null,
  };

  const response = await fetch(`${API_URL}/api/settings/`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    if (response.status === 403)
      return { errors: { _form: ["Admin access required"] } };
    const error = await response.json();
    return { errors: { _form: [error.detail || "Failed to save prompts"] } };
  }

  // Revalidate the prompts page to show updated values
  revalidatePath("/settings/prompts");

  return { success: true };
}

export async function getGenerationSettings(): Promise<GenerationSettings | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  const response = await fetch(`${API_URL}/api/settings/generation`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    if (response.status === 403) redirect("/dashboard?error=admin_required");
    return null;
  }

  return response.json();
}

export async function updateGenerationSettings(
  settings: Partial<GenerationSettings>
): Promise<{
  success: boolean;
  error?: string;
}> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    return { success: false, error: "Not authenticated" };
  }

  try {
    const response = await fetch(`${API_URL}/api/settings/generation`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    });

    if (!response.ok) {
      if (response.status === 401) redirect("/login");
      if (response.status === 403) {
        return { success: false, error: "Admin access required" };
      }
      const error = await response.json();
      return { success: false, error: error.detail || "Failed to update generation settings" };
    }

    return { success: true };
  } catch (error) {
    return { success: false, error: "Network error" };
  }
}
