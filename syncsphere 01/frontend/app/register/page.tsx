'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { identityApi } from '../../shared/services/api';
import { useAuthStore } from '../../shared/stores/authStore';
import { useOrgStore } from '../../shared/stores/orgStore';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/card';
import { Label } from '../../components/ui/label';
import { ShieldAlert, UserPlus } from 'lucide-react';
import { toast } from 'sonner';

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  first_name: z.string().min(2, 'First name is required'),
  last_name: z.string().min(2, 'Last name is required'),
  org_name: z.string().min(3, 'Organization name is required'),
  org_slug: z.string().min(3, 'Organization slug must be at least 3 characters')
    .regex(/^[a-z0-9-]+$/, 'Slug must contain only lowercase letters, numbers, and hyphens'),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const loginStore = useAuthStore((state) => state.login);
  const setOrgsStore = useOrgStore((state) => state.setOrgs);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setErrorMsg(null);
    setIsLoading(true);
    try {
      // Register the user
      await identityApi.register(values);

      // Auto-login after successful registration
      const { access_token } = await identityApi.login(values);
      localStorage.setItem("access_token", access_token);
      // Set session cookie on the FRONTEND domain so Next.js middleware
      // can detect authenticated users on subsequent navigations.
      document.cookie = "syncsphere-session=active; path=/; max-age=86400; samesite=lax";

      // Fetch user profile and org, then set stores
      loginStore(access_token, null as any);
      const user = await identityApi.getMe();
      loginStore(access_token, user);

      const org = await identityApi.getOrgs();
      setOrgsStore(Array.isArray(org) ? org : [org]);

      toast.success('Workspace Created', { description: `Welcome, ${user.first_name}! Your workspace is ready.` });
      router.push('/dashboard');
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.error?.message || 'Registration failed. Please try again.');
      toast.error('Registration Failed', { description: 'Failed to create tenant workspace.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOrgNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const slug = e.target.value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-');
    setValue('org_slug', slug);
  };

  return (
    <div className="flex relative h-screen w-screen items-center justify-center bg-background px-4 py-8 overflow-y-auto overflow-x-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[0%] right-[-10%] w-[40%] h-[50%] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />

      <Card className="z-10 w-full max-w-lg border-border/50 bg-card/60 shadow-[0_8px_32px_0_rgba(0,0,0,0.1)] backdrop-blur-xl my-auto transition-all duration-500">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="flex justify-center mb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground font-black text-xl shadow-[0_0_20px_rgba(var(--primary),0.25)] ring-1 ring-primary/20">
              S
            </div>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-foreground">Create Workspace Tenant</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Sign up to create an isolated organization workspace.
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

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="first_name" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">First Name</Label>
                <Input
                  id="first_name"
                  placeholder="John"
                  {...register('first_name')}
                  className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
                />
                {errors.first_name && <span className="text-[10px] text-rose-500 font-medium">{errors.first_name.message}</span>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="last_name" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Last Name</Label>
                <Input
                  id="last_name"
                  placeholder="Doe"
                  {...register('last_name')}
                  className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
                />
                {errors.last_name && <span className="text-[10px] text-rose-500 font-medium">{errors.last_name.message}</span>}
              </div>
            </div>

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
              <Label htmlFor="password" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Password (min 8 chars)</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                {...register('password')}
                className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
              />
              {errors.password && <span className="text-[10px] text-rose-500 font-medium">{errors.password.message}</span>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="org_name" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Organization Name</Label>
                <Input
                  id="org_name"
                  placeholder="Acme Corp"
                  {...register('org_name', { onChange: handleOrgNameChange })}
                  className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
                />
                {errors.org_name && <span className="text-[10px] text-rose-500 font-medium">{errors.org_name.message}</span>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="org_slug" className="text-xs font-semibold text-foreground/80 lowercase tracking-wide">Workspace Slug</Label>
                <Input
                  id="org_slug"
                  placeholder="acme-corp"
                  {...register('org_slug')}
                  className="h-11 bg-background/50 border-border/70 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-primary/30 placeholder-muted-foreground transition-all duration-300"
                />
                {errors.org_slug && <span className="text-[10px] text-rose-500 font-medium">{errors.org_slug.message}</span>}
              </div>
            </div>

            <Button type="submit" disabled={isLoading} className="w-full h-11 mt-4 bg-primary hover:bg-primary/90 text-primary-foreground flex items-center justify-center gap-2 shadow-lg shadow-primary/20 transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 font-medium">
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <>
                  <UserPlus className="h-4 w-4 transition-transform group-hover:translate-x-1" /> Create Workspace
                </>
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t border-border/40 pt-5 pb-5 text-center bg-muted/20">
          <p className="text-xs text-muted-foreground">
            Already have a workspace?{' '}
            <Link href="/login" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Sign In
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
