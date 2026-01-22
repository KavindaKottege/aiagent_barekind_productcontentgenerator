import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { decrypt } from "./session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  created_at: string;
}

// Verify session exists and return auth status
export const verifySession = cache(async () => {
  const cookieStore = await cookies();
  const cookie = cookieStore.get("session")?.value;

  if (!cookie) {
    redirect("/login");
  }

  const session = await decrypt(cookie);

  if (!session) {
    redirect("/login");
  }

  return { isAuth: true, userId: session.userId };
});

// Get current user from backend
export const getUser = cache(async (): Promise<User> => {
  const session = await verifySession();

  const cookieStore = await cookies();
  const cookie = cookieStore.get("session")?.value;

  const response = await fetch(`${API_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${cookie}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    redirect("/login");
  }

  return response.json();
});

// Get current admin user (redirects if not admin)
export const getAdmin = cache(async (): Promise<User> => {
  const user = await getUser();

  if (!user.is_admin) {
    redirect("/dashboard?error=admin_required");
  }

  return user;
});
