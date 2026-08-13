import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) => set({ accessToken: token, user, isAuthenticated: true }),
      logout: () => {
        if (typeof document !== 'undefined') {
          // Explicitly clear the Next.js middleware session tracking cookie
          document.cookie = "syncsphere-session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        }
        set({ accessToken: null, user: null, isAuthenticated: false });
      },
      updateUser: (userUpdates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userUpdates } : null,
        })),
    }),
    {
      name: 'syncsphere-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
