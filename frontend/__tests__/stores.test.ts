// Mock localStorage for Zustand persist middleware
const localStorageMock = (function () {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock window/document object for theme store and localStorage lookup
const documentMock = {
  documentElement: {
    classList: {
      add: jest.fn(),
      remove: jest.fn(),
    },
    style: {
      colorScheme: '',
    },
  },
};
Object.defineProperty(global, 'window', {
  value: {
    document: documentMock,
    localStorage: localStorageMock,
  },
  writable: true,
});

import { useAuthStore } from '../shared/stores/authStore';
import { useOrgStore } from '../shared/stores/orgStore';
import { useThemeStore } from '../shared/stores/themeStore';
import { useFeatureFlagStore } from '../shared/stores/featureFlagStore';
import { useNotificationStore } from '../shared/stores/notificationStore';
import { User, Organization } from '../shared/types';

describe('Zustand State Stores Unit Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
    useOrgStore.getState().clearOrgs();
    useNotificationStore.getState().clearNotifications();
  });

  // 1. Auth Store Tests
  test('AuthStore: login, updateUser and logout updates state correctly', () => {
    const mockUser: User = {
      id: 'u-1',
      email: 'user@acme.ai',
      first_name: 'John',
      last_name: 'Doe',
      org_id: 'org-1',
      role_ids: ['admin'],
      status: 'active',
      created_at: new Date().toISOString(),
    };

    const auth = useAuthStore.getState();
    expect(auth.isAuthenticated).toBe(false);
    expect(auth.accessToken).toBeNull();

    // Login
    auth.login('mock-jwt-token', mockUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().accessToken).toBe('mock-jwt-token');
    expect(useAuthStore.getState().user?.first_name).toBe('John');

    // Update profile
    useAuthStore.getState().updateUser({ first_name: 'Alice' });
    expect(useAuthStore.getState().user?.first_name).toBe('Alice');

    // Logout
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  // 2. Organization Store Tests
  test('OrgStore: setOrgs and setCurrentOrg updates organization context correctly', () => {
    const mockOrgs: Organization[] = [
      { id: 'org-1', name: 'Acme Corp', slug: 'acme-corp', created_at: new Date().toISOString() },
      { id: 'org-2', name: 'Stark Industries', slug: 'stark-ind', created_at: new Date().toISOString() },
    ];

    const orgStore = useOrgStore.getState();
    expect(orgStore.currentOrg).toBeNull();
    expect(orgStore.orgs).toHaveLength(0);

    // Set list
    orgStore.setOrgs(mockOrgs);
    expect(useOrgStore.getState().orgs).toHaveLength(2);
    // Auto select first
    expect(useOrgStore.getState().currentOrg?.id).toBe('org-1');

    // Switch active org
    useOrgStore.getState().setCurrentOrg(mockOrgs[1]);
    expect(useOrgStore.getState().currentOrg?.id).toBe('org-2');
  });

  // 3. Theme Store Tests
  test('ThemeStore: setTheme changes theme and updates document classes', () => {
    const themeStore = useThemeStore.getState();
    expect(themeStore.theme).toBe('dark'); // Default

    themeStore.setTheme('cyberpunk');
    expect(useThemeStore.getState().theme).toBe('cyberpunk');
    expect(window.document.documentElement.classList.add).toHaveBeenCalledWith('dark', 'theme-cyberpunk');
  });

  // 4. Feature Flags Store Tests
  test('FeatureFlagStore: updates individual flags and toggles state', () => {
    const flagStore = useFeatureFlagStore.getState();
    expect(flagStore.flags.enablePlanner).toBe(true);

    flagStore.setFlag('enablePlanner', false);
    expect(useFeatureFlagStore.getState().flags.enablePlanner).toBe(false);

    flagStore.setAllFlags({ enableKnowledge: false, enableApprovals: false });
    expect(useFeatureFlagStore.getState().flags.enableKnowledge).toBe(false);
    expect(useFeatureFlagStore.getState().flags.enableApprovals).toBe(false);
  });

  // 5. Notifications Store Tests
  test('NotificationStore: adds notification, updates counts and marks as read', () => {
    const notifStore = useNotificationStore.getState();
    expect(notifStore.notifications).toHaveLength(0);
    expect(notifStore.unreadCount).toBe(0);

    notifStore.addNotification({
      id: 'n-1',
      org_id: 'org-1',
      name: 'CPU Breach',
      message: 'Worker CPU is above 90%',
      severity: 'WARNING',
      status: 'ACTIVE',
    });

    expect(useNotificationStore.getState().notifications).toHaveLength(1);
    expect(useNotificationStore.getState().unreadCount).toBe(1);

    // Mark as Read
    useNotificationStore.getState().markAsRead('n-1');
    expect(useNotificationStore.getState().unreadCount).toBe(0);
    expect(useNotificationStore.getState().notifications[0].status).toBe('RESOLVED');
  });
});
