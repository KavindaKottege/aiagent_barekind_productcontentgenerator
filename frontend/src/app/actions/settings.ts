"use server";

import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Settings {
  openai_api_key: string | null;
  has_api_key: boolean;
}

export interface FormState {
  errors?: {
    openai_api_key?: string[];
    _form?: string[];
  };
  success?: boolean;
}

export async function getSettings(): Promise<Settings | null> {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("session")?.value;

    if (!sessionCookie) {
      throw new Error("Not authenticated");
    }

    const response = await fetch(`${API_URL}/settings/`, {
      headers: {
        Authorization: `Bearer ${sessionCookie}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch settings:", error);
    return null;
  }
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

  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("session")?.value;

    if (!sessionCookie) {
      return {
        errors: {
          _form: ["Not authenticated"],
        },
      };
    }

    const response = await fetch(`${API_URL}/settings/`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${sessionCookie}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ openai_api_key }),
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        errors: {
          _form: [error.detail || "Failed to update settings"],
        },
      };
    }

    return {
      success: true,
    };
  } catch (error) {
    return {
      errors: {
        _form: ["An unexpected error occurred. Please try again."],
      },
    };
  }
}
