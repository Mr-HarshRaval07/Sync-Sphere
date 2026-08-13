// ==========================================
// Module 14 — Admin Portal Unit Tests
// ==========================================

import { useAdminStore } from '../features/admin/stores/adminStore';
import { User, ApiKey } from '../shared/types';

describe('Admin Store Unit Tests', () => {
  beforeEach(() => {
    useAdminStore.setState({
      impersonatedUser: null,
      isImpersonating: false,
      activeSessions: [],
      members: [],
      invitations: [],
      roles: [],
      users: [],
      apiKeys: [],
      secrets: [],
      auditLogs: [],
      complianceItems: [
        { id: 'soc-1', framework: 'SOC2', controlName: 'Access Control Policies', status: 'compliant', description: 'Enforce MFA and IP restrictions.' },
      ],
      orgFeatureFlags: {
        enableAdvancedRouting: true,
        enableModelStreaming: false,
      },
      permissionInspector: {
        userId: '',
        resource: '',
        action: '',
        allowed: false,
      },
      quotaForecast: {
        currentUsage: 4120,
        projectedUsage: 5800,
        limit: 6000,
        growthPercentage: 14.5,
      },
      auditSearchQuery: '',
      activeAdminTab: 'org',
    });
  });

  // 1. Impersonation & Session
  test('startImpersonation sets state and audit logs start', () => {
    const mockUser: User = { id: 'u-2', email: 'dev@acme.ai', first_name: 'Dev', last_name: 'User', org_id: 'org-1', role_ids: [], status: 'active', created_at: '' };
    const store = useAdminStore.getState();

    expect(store.isImpersonating).toBe(false);
    expect(store.impersonatedUser).toBeNull();

    store.startImpersonation(mockUser);
    const state = useAdminStore.getState();
    expect(state.isImpersonating).toBe(true);
    expect(state.impersonatedUser?.id).toBe('u-2');
    expect(state.auditLogs).toHaveLength(1);
    expect(state.auditLogs[0].action).toBe('IMPERSONATE_USER_START');
  });

  test('stopImpersonation terminates state and audit logs end', () => {
    const mockUser: User = { id: 'u-2', email: 'dev@acme.ai', first_name: 'Dev', last_name: 'User', org_id: 'org-1', role_ids: [], status: 'active', created_at: '' };
    const store = useAdminStore.getState();

    store.startImpersonation(mockUser);
    expect(useAdminStore.getState().isImpersonating).toBe(true);

    useAdminStore.getState().stopImpersonation();
    const state = useAdminStore.getState();
    expect(state.isImpersonating).toBe(false);
    expect(state.impersonatedUser).toBeNull();
    expect(state.auditLogs).toHaveLength(2);
    expect(state.auditLogs[0].action).toBe('IMPERSONATE_USER_END');
  });

  test('revokeSession removes session by ID', () => {
    const store = useAdminStore.getState();
    store.setSessions([
      { id: 'sess-1', userId: 'u-2', userName: 'Dev', device: 'Chrome', ipAddress: '', location: '', activeSince: '' },
    ]);
    expect(useAdminStore.getState().activeSessions).toHaveLength(1);

    useAdminStore.getState().revokeSession('sess-1');
    expect(useAdminStore.getState().activeSessions).toHaveLength(0);
  });

  // 2. User Accounts Status
  test('updateUserStatus changes user state', () => {
    const mockUser: User = { id: 'u-2', email: 'dev@acme.ai', first_name: 'Dev', last_name: 'User', org_id: 'org-1', role_ids: [], status: 'active', created_at: '' };
    const store = useAdminStore.getState();
    store.setUsers([mockUser]);

    store.updateUserStatus('u-2', 'suspended');
    expect(useAdminStore.getState().users[0].status).toBe('suspended');
  });

  // 3. API Keys
  test('addApiKey appends key, revokeApiKey removes key', () => {
    const store = useAdminStore.getState();
    const mockKey: ApiKey = { id: 'k-1', name: 'CI key', key_prefix: 'sk_live_', created_at: '' };

    store.addApiKey(mockKey);
    expect(useAdminStore.getState().apiKeys).toHaveLength(1);

    useAdminStore.getState().revokeApiKey('k-1');
    expect(useAdminStore.getState().apiKeys).toHaveLength(0);
  });

  // 4. Feature Flags
  test('toggleFeatureFlag flips Boolean status', () => {
    const store = useAdminStore.getState();
    expect(store.orgFeatureFlags.enableModelStreaming).toBe(false);

    store.toggleFeatureFlag('enableModelStreaming');
    expect(useAdminStore.getState().orgFeatureFlags.enableModelStreaming).toBe(true);
  });

  // 5. Secrets Rotation
  test('rotateSecret marks status and logs rotation', () => {
    const store = useAdminStore.getState();
    store.setSecrets([
      { id: 'sec-1', name: 'OpenAI Token', provider: 'OpenAI', status: 'valid', lastRotated: '10 days ago', encryptionStatus: 'AES-256' },
    ]);

    store.rotateSecret('sec-1');
    const state = useAdminStore.getState();
    expect(state.secrets[0].status).toBe('rotated');
    expect(state.auditLogs[0].action).toBe('SECRET_ROTATED');
  });

  // 6. Permission Inspector
  test('inspectPermission evaluates user and resource scopes', () => {
    const store = useAdminStore.getState();
    
    // Admins are allowed
    store.inspectPermission('org-admin-1', 'secrets:token', 'write');
    expect(useAdminStore.getState().permissionInspector.allowed).toBe(true);

    // Guest not allowed for write
    useAdminStore.getState().inspectPermission('guest-1', 'secrets:token', 'write');
    expect(useAdminStore.getState().permissionInspector.allowed).toBe(false);
  });
});
