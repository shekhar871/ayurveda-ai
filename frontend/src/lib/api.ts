const API = import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "";

export type Health = {
  status: string;
  service: string;
  mode: string;
  layers: string[];
};

export type StackLayer = {
  name: string;
  role: string;
  status: string;
  error?: string;
};

export type CorpusStats = {
  verse_count: number;
  granthas: string[];
  conditions_indexed: string[];
  formulations_indexed: string[];
};

export type StackStatus = {
  mode: string;
  full_stack: boolean;
  corpus?: CorpusStats;
  layers: StackLayer[];
  data_stores: string[];
};

export type Remedy = {
  condition_confirmed: string;
  formulation_name: string;
  source_citation: string;
  modern_evidence_summary: string;
  duration_days: number;
};

export type QueryResult = {
  answer: string;
  remedies: Remedy[];
  citations: string[];
  grounded: boolean;
  safety_notes: string[];
  query_intent?: string;
  conditions_detected?: string[];
  query?: string;
  sources_used?: number;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail || res.statusText;
    if (res.status === 405) {
      throw new Error("Service unavailable. Please refresh and try again.");
    }
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  health: () => request<Health>("/health"),
  stackStatus: () => request<StackStatus>("/api/v1/status"),

  query: (query: string, userId?: string | null, season?: string) =>
    request<{ elapsed_ms: number; query: string; result: QueryResult }>("/api/v1/query", {
      method: "POST",
      body: JSON.stringify({ query, user_id: userId || null, season: season || null }),
    }),

  profile: (data: Record<string, unknown>) =>
    request<{ user_id: string }>("/api/v1/profile", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  feedback: (data: {
    user_id: string;
    formulation_name: string;
    outcome: string;
    checkpoint_day: number;
    notes?: string;
  }) =>
    request<{ status: string; efficacy_delta: number }>("/api/v1/feedback", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  progressFailure: (data: {
    user_id: string;
    current_protocol_id: string;
    observed_imbalance: string;
  }) =>
    request<Record<string, unknown>>("/api/v1/progress/failure", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  ingestSample: () =>
    request<{ ingested: number; verse_ids: number[] }>("/api/v1/ingest/sample", {
      method: "POST",
    }),

  retrieve: (q: string, limit = 5) =>
    request<{ hits: Record<string, unknown>[] }>(
      `/api/v1/retrieve?q=${encodeURIComponent(q)}&limit=${limit}`
    ),
};
