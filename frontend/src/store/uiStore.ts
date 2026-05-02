import { create } from "zustand";

interface UIState {
  isSyncing: boolean;
  setSyncing: (value: boolean) => void;

  activeTab: string;
  setActiveTab: (tab: string) => void;

  configDirty: boolean;
  setConfigDirty: (value: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSyncing: false,
  setSyncing: (value) => set({ isSyncing: value }),

  activeTab: "/",
  setActiveTab: (tab) => set({ activeTab: tab }),

  configDirty: false,
  setConfigDirty: (value) => set({ configDirty: value }),
}));
