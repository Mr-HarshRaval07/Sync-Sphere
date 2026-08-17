'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuthStore } from '../../shared/stores/authStore';
import { useOrgStore } from '../../shared/stores/orgStore';
import { identityApi } from '../../shared/services/api';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/card';
import { Label } from '../../components/ui/label';
import { ShieldAlert, LogIn } from 'lucide-react';
import { toast } from 'sonner';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const loginStore = useAuthStore((state) => state.login);
  const setOrgsStore = useOrgStore((state) => state.setOrgs);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMsg(null);
    setIsLoading(true);

    try {
      const res = await identityApi.login(values);
      const access_token = res.access_token;
      const refresh_token = res.refresh_token;

      localStorage.setItem("access_token", access_token);
      if (refresh_token) {
        localStorage.setItem("refresh_token", refresh_token);
      }
      // Set session cookie on the FRONTEND domain so Next.js middleware
      // can detect authenticated users on subsequent navigations.
      document.cookie = "syncsphere-session=active; path=/; max-age=86400; samesite=lax";

      // Login only returns tokens — fetch the user profile separately
      loginStore(access_token, null as any); // temp; replaced right below
      const user = await identityApi.getMe();
      loginStore(access_token, user);

      const org = await identityApi.getOrgs();
      // getOrgs() returns a single org object; wrap in array for the store
      setOrgsStore(Array.isArray(org) ? org : [org]);

      toast.success('Access Granted', { description: `Welcome back, ${user.first_name}!` });
      router.push('/dashboard');

      // Save login
      // Temporary compatibility with current backend response

    } catch (err: any) {
      console.error("LOGIN ERROR:", err);

      setErrorMsg(
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Login failed."
      );

      toast.error("Authentication Failed", {
        description:
          err?.response?.data?.detail ||
          err?.message ||
          "Please review login credentials.",
      });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="flex relative h-screen w-screen items-center justify-center bg-background px-4 overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[50%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[50%] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />

      <Card className="z-10 w-full max-w-md border-border/50 bg-card/60 shadow-[0_8px_32px_0_rgba(0,0,0,0.1)] backdrop-blur-xl transition-all duration-500">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="flex justify-center mb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground font-black text-xl shadow-[0_0_20px_rgba(var(--primary),0.25)] ring-1 ring-primary/20">
              S
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-foreground">SyncSphere Sign In</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Enter credentials to access agentic planning workspace.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {errorMsg && (
              <div className="flex items-center gap-2 rounded-md bg-rose-500/10 border border-rose-500/25 p-3 text-xs text-rose-500 font-medium">
                <ShieldAlert className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Work Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@acme.ai"
                {...register('email')}
                className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
              />
              {errors.email && <span className="text-[10px] text-rose-500 font-medium">{errors.email.message}</span>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                {...register('password')}
                className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
              />
              {errors.password && <span className="text-[10px] text-rose-500 font-medium">{errors.password.message}</span>}
            </div>

            <Button type="submit" disabled={isLoading} className="w-full h-11 mt-4 bg-primary hover:bg-primary/90 text-primary-foreground flex items-center justify-center gap-2 shadow-lg shadow-primary/20 transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 font-medium">
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <>
                  <LogIn className="h-4 w-4 transition-transform group-hover:translate-x-1" /> Sign In
                </>
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t border-border/40 pt-5 pb-5 text-center bg-muted/20">
          <p className="text-xs text-muted-foreground">
            Don&apos;t have a workspace organization?{' '}
            <Link href="/register" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Create one
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
