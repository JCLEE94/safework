import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Notification {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  message: string;
  duration?: number;
}

interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  mobileDrawerVisible: boolean;
  notifications: Notification[];
  globalLoading: boolean;
  loadingMessage?: string;
}

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
  mobileDrawerVisible: false,
  notifications: [],
  globalLoading: false,
  loadingMessage: undefined,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    toggleMobileDrawer: (state) => {
      state.mobileDrawerVisible = !state.mobileDrawerVisible;
    },
    setMobileDrawerVisible: (state, action: PayloadAction<boolean>) => {
      state.mobileDrawerVisible = action.payload;
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.push(action.payload);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setGlobalLoading: (state, action: PayloadAction<{ loading: boolean; message?: string }>) => {
      state.globalLoading = action.payload.loading;
      state.loadingMessage = action.payload.message;
    },
  },
});

export const {
  toggleTheme,
  setTheme,
  toggleSidebar,
  setSidebarCollapsed,
  toggleMobileDrawer,
  setMobileDrawerVisible,
  addNotification,
  removeNotification,
  clearNotifications,
  setGlobalLoading,
} = uiSlice.actions;

export default uiSlice.reducer;