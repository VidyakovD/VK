import { create } from "zustand";
import type { UserRead } from "@/api/client";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserRead | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserRead | null) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, refreshToken: null, user: null }),
}));
