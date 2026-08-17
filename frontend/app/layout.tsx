'use client';

import React from 'react';
import Script from 'next/script';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeatureFlagProvider } from '../shared/stores/featureFlagStore';
import './globals.css';

// Central React Query Client instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>SyncSphere AI - Multi-Agent Workflow Platform</title>
        <meta name="description" content="Enterprise multi-agent planning and runtime orchestration dashboard." />
        <link rel="icon" href="/favicon.ico" />
        <Script
          id="theme-initializer"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              try {
                let theme = 'dark';
                const stored = localStorage.getItem('syncsphere-theme');
                if (stored) {
                  const state = JSON.parse(stored).state;
                  if (state && state.theme) theme = state.theme;
                }
                document.documentElement.classList.add(theme);
                document.documentElement.style.colorScheme = theme;
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <FeatureFlagProvider>
            {children}
          </FeatureFlagProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
