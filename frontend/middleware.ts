import { NextResponse, NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  console.log("PATH:", request.nextUrl.pathname);
  console.log("ALL COOKIES");

  request.cookies.getAll().forEach(c => {
    console.log(c.name, c.value);
  });

  const { pathname } = request.nextUrl;

  // Let public assets and auth routes pass through
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname === '/favicon.ico' ||
    pathname === '/login' ||
    pathname === '/register'
  ) {
    return NextResponse.next();
  }

  // IMPORTANT: OAuth flows must never be interrupted by auth redirects.
  // Exclude provider initiation + callback endpoints (backend routes) and the post-callback landing page.
  if (
    pathname.startsWith('/connect') ||
    pathname.startsWith('/v1/connect') ||
    // Next.js middleware must allow the OAuth initiation + provider callback
    // endpoints under the same backend prefix.
    pathname.startsWith('/v1/connect/github') ||
    pathname.startsWith('/v1/connect/slack') ||
    pathname.startsWith('/dashboard/connectors') ||
    pathname.startsWith('/dashboard/connectors?')
  ) {
    return NextResponse.next();
  }



  // Session cookie check: the frontend JS sets a `syncsphere-session=active`
  // cookie on the FRONTEND domain after a successful login.  The backend's
  // HttpOnly access_token/refresh_token cookies live on localhost:8000 and are
  // NEVER sent to the frontend domain (localhost:3002), so we cannot use them
  // here.  The syncsphere-session cookie is the correct cross-origin signal.
  const hasSession =
    request.cookies.get("syncsphere-session")?.value === "active";

  // Redirect unauthenticated users to /login, but only for actual protected app routes.
  // OAuth routes are excluded above.
  if (pathname.startsWith('/dashboard') && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  // Also protect /connectors under dashboard prefix (safety)
  if (pathname.startsWith('/dashboard/connectors') && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  // Handle Root Index Page precisely matching current session context
  // The root path should ALWAYS render the home page to avoid redirect loops 
  // on stale session cookies. Actual background validation and redirect to 
  // dashboard will happen firmly from the client bundle (see page.tsx).
  if (pathname === '/') {
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
