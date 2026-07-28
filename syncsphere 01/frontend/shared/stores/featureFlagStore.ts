import { create } from 'zustand';

export interface FeatureFlags {
  enablePlanner: boolean;
  enableKnowledge: boolean;
  enableApprovals: boolean;
  enableObservability: boolean;
  enableSagaRollbacks: boolean;
  enableMcpConnectors: boolean;
}

interface FeatureFlagState {
  flags: FeatureFlags;
  setFlag: (key: keyof FeatureFlags, value: boolean) => void;
  setAllFlags: (flags: Partial<FeatureFlags>) => void;
}

export const useFeatureFlagStore = create<FeatureFlagState>((set) => ({
  flags: {
    enablePlanner: true,
    enableKnowledge: true,
    enableApprovals: true,
    enableObservability: true,
    enableSagaRollbacks: true,
    enableMcpConnectors: true,
  },
  setFlag: (key, value) =>
    set((state) => ({
      flags: {
        ...state.flags,
        [key]: value,
      },
    })),
  setAllFlags: (flagUpdates) =>
    set((state) => ({
      flags: {
        ...state.flags,
        ...flagUpdates,
      },
    })),
}));
import React from 'react';

export const FeatureFlagProvider = ({ children, initialFlags }: { children: React.ReactNode; initialFlags?: Partial<FeatureFlags> }) => {
  if (initialFlags) {
    useFeatureFlagStore.getState().setAllFlags(initialFlags);
  }
  return React.createElement(React.Fragment, null, children);
};
export const useFeatureFlags = () => useFeatureFlagStore((state) => state.flags);
