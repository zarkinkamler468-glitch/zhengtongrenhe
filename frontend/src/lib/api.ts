/** 线上同域部署时自动用当前站点 origin，避免构建时写死 localhost 导致 404 */
export function getApiBase(): string {
  const env = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/$/, "");
  if (typeof window !== "undefined") {
    if (!env || /localhost|127\.0\.0\.1/.test(env)) {
      return window.location.origin;
    }
    return env;
  }
  return env || "http://localhost:8000";
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const res = await fetch(`${getApiBase()}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("未授权");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
          : res.statusText;
    if (
      res.status === 403 &&
      typeof detail === "string" &&
      detail.includes("多用户模式") &&
      typeof window !== "undefined"
    ) {
      clearToken();
      window.location.href = "/login";
    }
    throw new Error(message || "请求失败");
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  getAuthConfig: async () => {
    const res = await fetch(`${getApiBase()}/api/v1/auth/config`);
    if (!res.ok) throw new Error("无法加载系统配置");
    return res.json() as Promise<{
      multi_user_enabled: boolean;
      allow_signup: boolean;
      allow_public_login: boolean;
    }>;
  },

  login: async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password });
    const res = await fetch(`${getApiBase()}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const detail = err.detail;
      const message =
        typeof detail === "string"
          ? detail
          : res.status === 403
            ? "账户已停用"
            : "用户名或密码错误";
      throw new Error(message);
    }
    return res.json() as Promise<{ access_token: string }>;
  },

  me: () => request<User>("/api/v1/auth/me"),

  signup: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) =>
    request<User>("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getQuota: () =>
    request<{
      crawl_quota: number;
      crawl_used: number;
      crawl_remaining: number;
      ai_quota: number;
      ai_used: number;
      ai_remaining: number;
    }>("/api/v1/auth/quota"),

  listAdminUsers: () => request<AdminUser[]>("/api/v1/admin/users"),

  getAdminSettings: () =>
    request<{ multi_user_enabled: boolean }>("/api/v1/admin/settings"),

  updateAdminSettings: (data: { multi_user_enabled: boolean }) =>
    request<{ multi_user_enabled: boolean }>("/api/v1/admin/settings", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  updateAdminUser: (
    id: number,
    data: {
      crawl_quota?: number;
      ai_quota?: number;
      crawl_used?: number;
      ai_used?: number;
      is_active?: boolean;
    }
  ) =>
    request<AdminUser>(`/api/v1/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getArticles: (params?: {
    skip?: number;
    limit?: number;
    policy_level?: string;
    project_category?: string;
    source_name?: string;
    has_analysis?: boolean;
    policy_type?: string;
    q?: string;
  }) => {
    const sp = new URLSearchParams();
    const p = params ?? {};
    sp.set("skip", String(p.skip ?? 0));
    sp.set("limit", String(p.limit ?? 20));
    if (p.policy_level) sp.set("policy_level", p.policy_level);
    if (p.project_category) sp.set("project_category", p.project_category);
    if (p.source_name) sp.set("source_name", p.source_name);
    if (p.has_analysis !== undefined) sp.set("has_analysis", String(p.has_analysis));
    if (p.policy_type) sp.set("policy_type", p.policy_type);
    if (p.q) sp.set("q", p.q);
    return request<ArticleListResponse>(`/api/v1/articles?${sp}`);
  },

  getArticleOverview: () => request<ArticleOverview>("/api/v1/articles/overview"),

  getArticleSources: () => request<{ sources: string[] }>("/api/v1/articles/sources"),

  analyzeArticle: (id: number, force = false) =>
    request<{
      status: string;
      task_id?: string;
      force?: boolean;
      article_id?: number;
    }>(`/api/v1/articles/${id}/analyze?force=${force}`, { method: "POST" }),

  getArticle: (id: number) => request<ArticleDetail>(`/api/v1/articles/${id}`),

  searchArticles: (q: string, skip = 0, limit = 20) =>
    request<SearchResult>(`/api/v1/articles/search?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),

  getMonitorStats: () => request<MonitorStats>("/api/v1/monitor/stats"),

  toggleSource: (sourceId: number) =>
    request<{ status: string; running: boolean }>(`/api/v1/monitor/sources/${sourceId}/toggle`, {
      method: "POST",
    }),

  triggerSourceCrawl: (sourceId: number) =>
    request<{
      status?: string;
      count: number;
      column_ids: number[];
      results?: Array<{
        column_id: number;
        status?: string;
        new?: number;
        updated?: number;
        listed?: number;
        skipped_by_filter?: number;
        hint?: string;
        error?: string;
      }>;
    }>(`/api/v1/monitor/sources/${sourceId}/crawl`, { method: "POST" }),

  enableAllAndStart: () =>
    request<{
      enabled_sources: number;
      enabled_columns: number;
      count: number;
      status?: string;
      results?: Array<{
        column_id: number;
        status?: string;
        new?: number;
        updated?: number;
        listed?: number;
        skipped_by_filter?: number;
        hint?: string;
        error?: string;
      }>;
    }>("/api/v1/monitor/batch/enable-and-start", { method: "POST" }),

  pauseAllSources: () =>
    request<{ paused_sources: number }>("/api/v1/monitor/batch/pause-all", { method: "POST" }),

  deleteSource: (sourceId: number) =>
    request<{ status: string; name: string }>(`/api/v1/monitor/sources/${sourceId}`, { method: "DELETE" }),

  deletePausedSources: () =>
    request<{ deleted: number; names: string[] }>("/api/v1/monitor/batch/paused", { method: "DELETE" }),

  getSources: () => request<SourceMonitor[]>("/api/v1/monitor/sources"),

  getMonitorTree: () => request<MonitorTreeSource[]>("/api/v1/monitor/tree"),

  bootstrapMonitor: () =>
    request<{ tree: MonitorTreeSource[]; tasks: CrawlTask[]; stats: MonitorStats }>(
      "/api/v1/monitor/bootstrap"
    ),

  getCrawlTasks: () => request<CrawlTask[]>("/api/v1/monitor/tasks"),

  createCrawlTask: (data: CrawlTaskCreate) =>
    request<CrawlTask>("/api/v1/monitor/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteCrawlTask: (taskId: number) =>
    request<{ status: string; name: string }>(`/api/v1/monitor/tasks/${taskId}`, { method: "DELETE" }),

  toggleCrawlTask: (taskId: number) =>
    request<CrawlTask>(`/api/v1/monitor/tasks/${taskId}/toggle`, { method: "POST" }),

  startCrawlTask: (taskId: number) =>
    request<{
      status?: string;
      count: number;
      results?: Array<{
        column_id: number;
        status?: string;
        new?: number;
        updated?: number;
        listed?: number;
        skipped_by_filter?: number;
        hint?: string;
        error?: string;
      }>;
    }>(`/api/v1/monitor/tasks/${taskId}/start`, { method: "POST" }),

  pauseAllTasks: () =>
    request<{ paused_tasks: number }>("/api/v1/monitor/batch/tasks/pause-all", { method: "POST" }),

  deletePausedTasks: () =>
    request<{ deleted: number; names: string[] }>("/api/v1/monitor/batch/tasks/paused", {
      method: "DELETE",
    }),

  syncPresetSources: () =>
    request<{
      created_sources: number;
      created_columns: number;
      updated_sources: number;
      updated_columns: number;
      total_sources: number;
    }>("/api/v1/monitor/seed", { method: "POST" }),

  getColumnHealth: (sourceId?: number, columnIds?: number[]) => {
    const sp = new URLSearchParams();
    if (sourceId) sp.set("source_id", String(sourceId));
    if (columnIds?.length) sp.set("column_ids", columnIds.join(","));
    const q = sp.toString();
    return request<ColumnHealth[]>(`/api/v1/monitor/columns/health${q ? `?${q}` : ""}`);
  },

  getColumns: (sourceId?: number) =>
    request<MonitorColumn[]>(
      sourceId ? `/api/v1/monitor/columns?source_id=${sourceId}` : "/api/v1/monitor/columns"
    ),

  updateColumn: (columnId: number, data: Partial<MonitorColumnUpdate>) =>
    request<MonitorColumn>(`/api/v1/monitor/columns/${columnId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  bulkSchedule: (data: BulkScheduleRequest) =>
    request<{ updated: number }>("/api/v1/monitor/columns/bulk-schedule", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  toggleColumnAuto: (columnId: number) =>
    request<{ auto_crawl_enabled: boolean; schedule_label: string }>(
      `/api/v1/monitor/columns/${columnId}/toggle-auto`,
      { method: "POST" }
    ),

  toggleColumnActive: (columnId: number) =>
    request<{ is_active: boolean }>(`/api/v1/monitor/columns/${columnId}/toggle-active`, {
      method: "POST",
    }),

  triggerCrawl: (columnId: number) =>
    request<{ task_id: string }>(`/api/v1/monitor/columns/${columnId}/crawl`, { method: "POST" }),

  triggerBatchCrawl: (columnIds: number[]) =>
    request<{
      task_id?: string;
      count: number;
      column_ids: number[];
      status?: string;
      results?: Array<{
        column_id: number;
        status?: string;
        new?: number;
        updated?: number;
        listed?: number;
        skipped_by_filter?: number;
        hint?: string;
        error?: string;
      }>;
    }>("/api/v1/monitor/crawl/batch", {
      method: "POST",
      body: JSON.stringify({ column_ids: columnIds }),
    }),

  seedSources: () =>
    request<{ created_sources: number; created_columns: number }>("/api/v1/monitor/seed", {
      method: "POST",
    }),

  getSubscriptions: () => request<Subscription[]>("/api/v1/subscriptions"),

  getPushLogs: () => request<PushLog[]>("/api/v1/subscriptions/push-logs"),

  createSubscription: (data: SubscriptionInput) =>
    request<Subscription>("/api/v1/subscriptions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSubscription: (id: number, data: Partial<SubscriptionInput> & { is_active?: boolean }) =>
    request<Subscription>(`/api/v1/subscriptions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  testPushChannel: (data: SubscriptionInput & { keyword?: string }) =>
    request<{ success: boolean; message: string | null }>("/api/v1/subscriptions/test", {
      method: "POST",
      body: JSON.stringify({
        channel: data.channel,
        channel_config: data.channel_config ?? null,
        keyword: data.keyword ?? "测试关键词",
      }),
    }),

  deleteSubscription: (id: number) =>
    request(`/api/v1/subscriptions/${id}`, { method: "DELETE" }),

  getAnalytics: () => request<AnalyticsOverview>("/api/v1/analytics/overview"),

  askQA: (question: string) =>
    request<QAResponse>("/api/v1/qa/ask", {
      method: "POST",
      body: JSON.stringify({ question, limit: 5 }),
    }),

  getCrawlLogs: () => request<CrawlLog[]>("/api/v1/logs/crawl?limit=20"),
};

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  roles: string[];
  crawl_quota?: number;
  crawl_used?: number;
  ai_quota?: number;
  ai_used?: number;
}

export interface AdminUser extends User {
  is_active: boolean;
  crawl_quota: number;
  crawl_used: number;
  ai_quota: number;
  ai_used: number;
  created_at: string;
}

export interface ArticleListItem {
  id: number;
  title: string;
  publish_time: string | null;
  publisher: string | null;
  source_name: string | null;
  article_url: string;
  policy_level: string;
  project_category?: string | null;
  has_analysis: boolean;
  summary_preview?: string | null;
  policy_type?: string | null;
  keywords?: string[] | null;
  created_at: string;
}

export interface ArticleListResponse {
  total: number;
  items: ArticleListItem[];
}

export interface ArticleOverview {
  total: number;
  analyzed: number;
  pending: number;
  recent_7d: number;
  by_level: Record<string, number>;
  by_category: Record<string, number>;
  by_policy_type: Record<string, number>;
  top_sources: { name: string; count: number }[];
}

export interface ArticleDetail extends ArticleListItem {
  content: string | null;
  updated_at: string;
  attachments: { id: number; file_name: string; file_url: string; file_type: string | null }[];
  analysis: {
    summary_100: string | null;
    summary_300: string | null;
    summary_page: string | null;
    tags: Record<string, string> | null;
    keywords: string[] | null;
    key_info: Record<string, string | null> | null;
    analysis: Record<string, string> | null;
  } | null;
}

export interface SearchResult {
  total: number;
  items: ArticleListItem[];
  query: string;
}

export interface SourceMonitor {
  id: number;
  name: string;
  url: string;
  type: string;
  status: string;
  created_at: string;
}

export type ScheduleType = "interval" | "daily" | "manual";
export type CrawlFilterMode = "column" | "keyword" | "date_range";

export interface ColumnHealth {
  column_id: number;
  source_id: number;
  column_name: string;
  column_url: string;
  status: "ok" | "empty" | "error";
  http_ok: boolean;
  list_count: number;
  message: string;
}

export interface MonitorColumn {
  id: number;
  source_id: number;
  column_name: string;
  column_url: string;
  column_type: string;
  crawl_interval: number;
  schedule_type: ScheduleType;
  daily_crawl_time: string | null;
  auto_crawl_enabled: boolean;
  is_active: boolean;
  schedule_label: string;
  filter_label: string;
  crawl_filter_mode: CrawlFilterMode;
  filter_keywords: string[] | null;
  filter_date_from: string | null;
  filter_date_to: string | null;
  last_crawled_at: string | null;
}

export interface MonitorStats {
  active_sources: number;
  total_sources: number;
  total_columns: number;
  total_tasks?: number;
  running_tasks: number;
  today_collected: number;
}

export interface MonitorTreeSource {
  id: number;
  name: string;
  url: string;
  type: string;
  status: string;
  is_preset?: boolean;
  column_count?: number;
  task_count?: number;
  article_count?: number;
  today_new_count?: number;
  frequency_label?: string;
  last_crawled_at?: string | null;
  running?: boolean;
  columns: MonitorColumn[];
}

export interface CrawlTask {
  id: number;
  name: string;
  source_id: number;
  source_name: string;
  source_url: string;
  column_ids: number[];
  column_names: string[];
  schedule_type: ScheduleType;
  crawl_interval: number;
  daily_crawl_time: string | null;
  auto_crawl_enabled: boolean;
  crawl_filter_mode: CrawlFilterMode;
  filter_keywords: string[] | null;
  filter_date_from: string | null;
  filter_date_to: string | null;
  is_active: boolean;
  schedule_label: string;
  filter_label: string;
  last_crawled_at: string | null;
  created_at: string;
  running: boolean;
}

export interface CrawlTaskCreate {
  name?: string;
  source_id: number;
  column_ids: number[];
  schedule_type: ScheduleType;
  crawl_interval?: number;
  daily_crawl_time?: string;
  auto_crawl_enabled?: boolean;
  is_active?: boolean;
  crawl_filter_mode?: CrawlFilterMode;
  filter_keywords?: string[];
  filter_date_from?: string;
  filter_date_to?: string;
}

export interface MonitorColumnUpdate {
  schedule_type?: ScheduleType;
  crawl_interval?: number;
  daily_crawl_time?: string;
  auto_crawl_enabled?: boolean;
  is_active?: boolean;
}

export interface BulkScheduleRequest {
  column_ids: number[];
  schedule_type?: ScheduleType;
  crawl_interval?: number;
  daily_crawl_time?: string;
  auto_crawl_enabled?: boolean;
  is_active?: boolean;
  crawl_filter_mode?: CrawlFilterMode;
  filter_keywords?: string[];
  filter_date_from?: string;
  filter_date_to?: string;
}

export type PushChannelType =
  | "email"
  | "webhook"
  | "dingtalk"
  | "feishu"
  | "wechat_work"
  | "wechat_mp";

export interface SubscriptionInput {
  keyword: string;
  channel: PushChannelType;
  channel_config?: string | null;
}

export interface Subscription {
  id: number;
  keyword: string;
  channel: PushChannelType;
  channel_config: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PushLog {
  id: number;
  article_id: number;
  keyword: string;
  channel: PushChannelType;
  status: string;
  message: string | null;
  created_at: string;
}

export interface AnalyticsOverview {
  policy_stats: { today: number; this_week: number; this_month: number; total: number };
  industry_stats: { name: string; count: number }[];
  hot_words: { keyword: string; count: number; trend: string }[];
}

export interface QAResponse {
  question: string;
  answer: string;
  related_articles: { id: number; title: string; url: string; source: string | null }[];
}

export interface CrawlLog {
  id: number;
  column_id: number;
  column_name?: string | null;
  source_name?: string | null;
  status: string;
  new_count: number;
  updated_count: number;
  error_message: string | null;
  created_at: string;
}
