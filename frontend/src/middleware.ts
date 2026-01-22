import { NextRequest, NextResponse } from "next/server";

// Public paths that don't require authentication
const publicPaths = ["/login", "/signup", "/forgot-password", "/reset-password"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if current path is public
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path));

  // Get session cookie
  const sessionCookie = request.cookies.get("session");

  // If public path, allow through
  if (isPublicPath) {
    return NextResponse.next();
  }

  // If protected path and no session, redirect to login
  if (!sessionCookie) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Session exists, allow through (DAL will do real verification)
  return NextResponse.next();
}

// Matcher config to exclude static files, api routes, and Next.js internals
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*$).*)",
  ],
};
