import { NextRequest, NextResponse } from "next/server";

// Public paths that don't require authentication
const publicPaths = ["/login", "/signup", "/forgot-password", "/reset-password"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if current path is public
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path));

  // Get access token cookie (used by auth system)
  const accessToken = request.cookies.get("access_token");

  // Handle root path - redirect based on auth status
  if (pathname === "/") {
    if (accessToken) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    } else {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  // If public path, allow through
  if (isPublicPath) {
    return NextResponse.next();
  }

  // If protected path and no access token, redirect to login
  if (!accessToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Access token exists, allow through (DAL will do real verification)
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
