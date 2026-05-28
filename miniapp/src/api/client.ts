import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";

const baseURL = import.meta.env.VITE_API_URL || "";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 60_000,
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
      useAuthStore.getState().clear();
    }
    return Promise.reject(error);
  },
);

// =============================================================================
// Types
// =============================================================================
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

export interface CommunityRead {
  id: string;
  vk_group_id: number;
  group_name: string | null;
  group_avatar: string | null;
  is_active: boolean;
  connected_at: string;
}

export interface AgentRead {
  id: string;
  community_id: string;
  name: string;
  role: string;
  system_prompt: string | null;
  tone: string | null;
  llm_provider: string;
  llm_model: string | null;
  temperature: string;
  confidence_threshold: string;
  fallback_action: string | null;
  is_active: boolean;
  created_at: string;
}

export interface DocumentRead {
  id: string;
  agent_id: string;
  source_type: string;
  source_url: string | null;
  file_name: string | null;
  file_size: number | null;
  chunks_count: number | null;
  qdrant_collection: string | null;
  indexed_at: string | null;
  created_at: string;
}

export interface ChatSource {
  text: string;
  score: number;
  document_id: string;
  chunk_index: number;
}

export interface ChatResponse {
  text: string;
  sources: ChatSource[];
  confidence: number;
  tokens_in: number;
  tokens_out: number;
  credits_spent: string;
  model: string;
  provider: string;
  fallback_triggered: boolean;
  conversation_id: string;
}

export interface BalanceRead {
  credits_balance: string;
  trial_ends_at: string | null;
}

export interface TransactionRead {
  id: string;
  type: string;
  amount: string;
  balance_after: string | null;
  description: string | null;
  resource_type: string | null;
  created_at: string;
}

export interface PricingRuleRead {
  resource_type: string;
  credits_cost: string;
  description: string | null;
}

// =============================================================================
// Endpoints
// =============================================================================

// auth
export const authVK = (launchParams: string) =>
  api.post<TokenPair>("/api/auth/vk", { launch_params: launchParams }).then((r) => r.data);

export const getMe = () => api.get<UserRead>("/api/auth/me").then((r) => r.data);

// communities
export const listCommunities = () =>
  api.get<CommunityRead[]>("/api/communities").then((r) => r.data);

export const createCommunity = (body: {
  vk_group_id: number;
  group_name: string;
}) => api.post<CommunityRead>("/api/communities", body).then((r) => r.data);

export const deleteCommunity = (id: string) =>
  api.delete(`/api/communities/${id}`).then((r) => r.data);

// agents
export const listAgents = () => api.get<AgentRead[]>("/api/agents").then((r) => r.data);

export const createAgent = (body: {
  community_id: string;
  name: string;
  role: string;
  system_prompt?: string;
  tone?: string;
  llm_provider?: string;
  llm_model?: string;
  temperature?: number;
}) => api.post<AgentRead>("/api/agents", body).then((r) => r.data);

export const getAgent = (id: string) => api.get<AgentRead>(`/api/agents/${id}`).then((r) => r.data);

export const updateAgent = (id: string, body: Partial<AgentRead>) =>
  api.put<AgentRead>(`/api/agents/${id}`, body).then((r) => r.data);

export const deleteAgent = (id: string) =>
  api.delete(`/api/agents/${id}`).then((r) => r.data);

// knowledge base
export const listKB = (agentId: string) =>
  api.get<DocumentRead[]>(`/api/agents/${agentId}/knowledge`).then((r) => r.data);

export const uploadKBFile = (agentId: string, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post<DocumentRead>(`/api/agents/${agentId}/knowledge/file`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const uploadKBUrl = (agentId: string, url: string) =>
  api.post<DocumentRead>(`/api/agents/${agentId}/knowledge/url`, { url }).then((r) => r.data);

export const uploadKBManual = (agentId: string, title: string, content_text: string) =>
  api
    .post<DocumentRead>(`/api/agents/${agentId}/knowledge/manual`, { title, content_text })
    .then((r) => r.data);

export const deleteKB = (agentId: string, docId: string) =>
  api.delete(`/api/agents/${agentId}/knowledge/${docId}`).then((r) => r.data);

// chat
export const chatWithAgent = (
  agentId: string,
  body: { message: string; history?: { role: "user" | "assistant"; content: string }[]; top_k?: number },
) => api.post<ChatResponse>(`/api/agents/${agentId}/chat`, body).then((r) => r.data);

// conversations
export interface ConversationRead {
  id: string;
  agent_id: string;
  subscriber_id: string | null;
  messages: Array<{ role: string; content: string; timestamp?: string }>;
  tokens_in: number | null;
  tokens_out: number | null;
  credits_spent: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export const listConversations = (agentId: string) =>
  api.get<ConversationRead[]>(`/api/agents/${agentId}/conversations`).then((r) => r.data);

// billing
export const getBalance = () => api.get<BalanceRead>("/api/billing/balance").then((r) => r.data);

export const listTransactions = (limit = 50) =>
  api
    .get<TransactionRead[]>(`/api/billing/transactions?limit=${limit}`)
    .then((r) => r.data);

export const listPricing = () =>
  api.get<PricingRuleRead[]>("/api/billing/pricing").then((r) => r.data);
