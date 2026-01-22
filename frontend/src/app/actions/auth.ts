"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { signupSchema, loginSchema } from "@/lib/schemas";
import { setSession, clearSession, encrypt } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormState {
  errors?: {
    [key: string]: string[];
  };
}

// Signup action
export async function signup(
  state: FormState,
  formData: FormData
): Promise<FormState> {
  // Parse and validate form data
  const validatedFields = signupSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
    confirmPassword: formData.get("confirmPassword"),
  });

  // Return field errors if validation fails
  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  const { name, email, password } = validatedFields.data;

  try {
    // Call backend API
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        errors: {
          _form: [error.detail || "Failed to create account"],
        },
      };
    }

    const data = await response.json();

    // Set session cookie with JWT from backend
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days
    const sessionToken = await encrypt({
      userId: data.user.id,
      expiresAt,
    });

    await setSession(sessionToken);

    // Redirect to dashboard
    redirect("/dashboard");
  } catch (error) {
    return {
      errors: {
        _form: ["An unexpected error occurred. Please try again."],
      },
    };
  }
}

// Login action
export async function login(
  state: FormState,
  formData: FormData
): Promise<FormState> {
  // Parse and validate form data
  const validatedFields = loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  // Return field errors if validation fails
  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  const { email, password } = validatedFields.data;

  try {
    // Call backend API using OAuth2PasswordRequestForm format
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: email, // OAuth2 convention uses "username" field
        password: password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        errors: {
          _form: [error.detail || "Invalid email or password"],
        },
      };
    }

    const data = await response.json();

    // Set session cookie with JWT from backend
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days
    const sessionToken = await encrypt({
      userId: data.user.id,
      expiresAt,
    });

    await setSession(sessionToken);

    // Redirect to dashboard
    redirect("/dashboard");
  } catch (error) {
    return {
      errors: {
        _form: ["An unexpected error occurred. Please try again."],
      },
    };
  }
}

// Logout action
export async function logout() {
  await clearSession();
  redirect("/login");
}
