import { create } from 'zustand';
import { Alert } from '../types';

interface NotificationState {
  notifications: Alert[];
  unreadCount: number;
  addNotification: (alert: Omit<Alert, 'created_at'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (alert) =>
    set((state) => {
      const newAlert: Alert = {
        ...alert,
        created_at: new Date().toISOString(),
      };
      return {
        notifications: [newAlert, ...state.notifications],
        unreadCount: state.unreadCount + 1,
      };
    }),
  markAsRead: (id) =>
    set((state) => {
      const isUnread = state.notifications.find((n) => n.id === id)?.status === 'ACTIVE';
      const updated = state.notifications.map((n) =>
        n.id === id ? { ...n, status: 'RESOLVED' as const } : n
      );
      return {
        notifications: updated,
        unreadCount: isUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
      };
    }),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, status: 'RESOLVED' as const })),
      unreadCount: 0,
    })),
  clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
}));
