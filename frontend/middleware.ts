import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define route types
const publicRoutes = ['/', '/session-timeout'];
const authRoutes = ['/']; // Routes that authenticated users shouldn't access
const protectedRoutes = [
  '/dashboard',
  '/accounts',
  '/transactions',
  '/budget',
  '/cards',
  '/goals',
  '/transfer',
  '/p2p',
  '/business',
  '/subscriptions',
  '/security',
  '/settings',
  '/analytics',
  '/analytics-dashboard',
  '/invoices',
  '/credit-cards',
  '/investments',
  '/currency-converter',
  '/crypto',
  '/loans',
  '/insurance'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Allow access to static files, API routes, and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.includes('.') // static files
  ) {
    return NextResponse.next();
  }

  // Special handling for session-timeout page
  if (pathname === '/session-timeout') {
    // Clear any auth cookies when accessing session-timeout
    const response = NextResponse.next();
    response.cookies.delete('authToken');
    return response;
  }

  // Check for auth token in cookies
  const authToken = request.cookies.get('authToken')?.value;
  const isAuthenticated = !!authToken;

  // Handle 404 - always accessible
  if (!publicRoutes.includes(pathname) && !protectedRoutes.includes(pathname) && pathname !== '/not-found') {
    return NextResponse.next(); // Let Next.js handle 404
  }

  // Redirect authenticated users away from auth pages
  if (isAuthenticated && authRoutes.includes(pathname)) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Redirect unauthenticated users away from protected pages
  if (!isAuthenticated && protectedRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};