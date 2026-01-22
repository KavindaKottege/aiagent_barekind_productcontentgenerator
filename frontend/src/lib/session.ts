import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";

const SESSION_SECRET = process.env.SESSION_SECRET || "dev-secret-min-32-chars-long-for-jose";
const encodedKey = new TextEncoder().encode(SESSION_SECRET);

export interface SessionPayload {
  userId: string;
  expiresAt: Date;
}

// Encrypt session payload into JWT
export async function encrypt(payload: SessionPayload): Promise<string> {
  return new SignJWT({ userId: payload.userId })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(payload.expiresAt)
    .sign(encodedKey);
}

// Decrypt JWT and return session payload
export async function decrypt(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, encodedKey, {
      algorithms: ["HS256"],
    });
    return {
      userId: payload.userId as string,
      expiresAt: new Date((payload.exp as number) * 1000),
    };
  } catch (error) {
    console.error("Failed to verify session:", error);
    return null;
  }
}

// Get current session from cookies
export async function getSession(): Promise<SessionPayload | null> {
  const cookieStore = await cookies();
  const cookie = cookieStore.get("session")?.value;
  if (!cookie) return null;
  return await decrypt(cookie);
}

// Set session cookie
export async function setSession(token: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set("session", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: "/",
  });
}

// Clear session cookie
export async function clearSession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete("session");
}
