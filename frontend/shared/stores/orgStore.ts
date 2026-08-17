import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Organization } from '../types';

interface OrgState {
  currentOrg: Organization | null;
  orgs: Organization[];
  setCurrentOrg: (org: Organization | null) => void;
  setOrgs: (orgs: Organization[]) => void;
  clearOrgs: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      currentOrg: null,
      orgs: [],
      setCurrentOrg: (org) => set({ currentOrg: org }),
      setOrgs: (orgs) => set((state) => ({ orgs, currentOrg: state.currentOrg || orgs[0] || null })),
      clearOrgs: () => set({ currentOrg: null, orgs: [] }),
    }),
    {
      name: 'syncsphere-org',
      merge: (persisted: any, current: OrgState): OrgState => ({
        ...current,
        ...persisted,
        // Sanitize stale stored data — orgs must always be an array
        orgs: Array.isArray(persisted?.orgs) ? persisted.orgs : [],
      }),
    }
  )
);
