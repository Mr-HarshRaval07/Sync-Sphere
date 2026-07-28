'use client';

import React from 'react';
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
    <html lang="en">
      <head>
        <title>SyncSphere AI - Multi-Agent Workflow Platform</title>
        <meta name="description" content="Enterprise multi-agent planning and runtime orchestration dashboard." />
        <link rel="icon" href="/favicon.ico" />
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
