import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";

const baseURL = import.meta.env.VITE_API_URL || "";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30_000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // TODO: trigger refresh flow once /api/auth/refresh exists.
      useAuthStore.getState().clear();
    }
    return Promise.reject(error);
  },
);

// --- Typed endpoints ---------------------------------------------------------
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserRead {
  id: string;
  vk_id: number;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  credits_balance: string;
}

export async function authVK(launchParams: string): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/api/auth/vk", { launch_params: launchParams });
  return data;
}

export async function getMe(): Promise<UserRead> {
  const { data } = await api.get<UserRead>("/api/auth/me");
  return data;
}
