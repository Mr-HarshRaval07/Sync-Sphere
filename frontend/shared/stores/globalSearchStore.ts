import { create } from 'zustand';

interface GlobalSearchState {
  isOpen: boolean;
  toggle: () => void;
  setOpen: (open: boolean) => void;
}

export const useGlobalSearchStore = create<GlobalSearchState>((set) => ({
  isOpen: false,
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (open) => set({ isOpen: open }),
}));
export const useGlobalSearch = () => useGlobalSearchStore();
