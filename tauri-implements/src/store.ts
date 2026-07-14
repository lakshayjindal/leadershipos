import { create } from 'zustand';
import type { TodayStatus, AppConfiguration, AppState, Task, WorkSession } from './types';

export type WorkspaceView = 'today' | 'history' | 'settings';

interface OverlayState {
  searchOpen: boolean;
  commandPaletteOpen: boolean;
  morningGreeting: boolean;
  recoveryOverlay: boolean;
}

interface AppStore {
  // Core state
  todayStatus: TodayStatus | null;
  config: AppConfiguration | null;
  theme: 'dark' | 'light';

  // Navigation
  currentState: AppState;
  workspaceView: WorkspaceView;

  // Overlays
  overlays: OverlayState;

  // Actions
  setTodayStatus: (status: TodayStatus) => void;
  setConfig: (config: AppConfiguration) => void;
  setTheme: (theme: 'dark' | 'light') => void;
  setCurrentState: (state: AppState) => void;
  setWorkspaceView: (view: WorkspaceView) => void;
  toggleOverlay: (key: keyof OverlayState) => void;
  setOverlay: (key: keyof OverlayState, open: boolean) => void;
  closeAllOverlays: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  todayStatus: null,
  config: null,
  theme: 'dark',
  currentState: 'idle',
  workspaceView: 'today',
  overlays: {
    searchOpen: false,
    commandPaletteOpen: false,
    morningGreeting: false,
    recoveryOverlay: false,
  },

  setTodayStatus: (status) =>
    set({ todayStatus: status }),

  setConfig: (config) =>
    set({ config }),

  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },

  setCurrentState: (state) => {
    // When switching to a non-today view, preserve the state
    set((s) => {
      const newState = { ...s, currentState: state };
      // If going to review, ensure workspace view is 'today'
      if (state === 'review') {
        newState.workspaceView = 'today';
      }
      return newState;
    });
  },

  setWorkspaceView: (view) =>
    set({ workspaceView: view }),

  toggleOverlay: (key) =>
    set((s) => ({
      overlays: { ...s.overlays, [key]: !s.overlays[key] },
    })),

  setOverlay: (key, open) =>
    set((s) => ({
      overlays: { ...s.overlays, [key]: open },
    })),

  closeAllOverlays: () =>
    set({
      overlays: {
        searchOpen: false,
        commandPaletteOpen: false,
        morningGreeting: false,
        recoveryOverlay: false,
      },
    }),
}));
