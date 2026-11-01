// Typed API client for the RiskLens backend. A thin fetch wrapper attaches the
// Bearer token stored in localStorage and normalises error handling so callers
// always receive either typed data or a thrown ApiError they can catch.

import type {
  AddHoldingRequest,
  Alert,
  AuthResponse,
  BuilderRequest,
  BuilderResult,
  Cashflow,
  DashboardKPIs,
  Holding,
  InstrumentDetail,
  InstrumentSummary,
  LiquidityDetail,
  NewsItem,
  Paginated,
  PortfolioCashflows,
  PortfolioDetail,
  PortfolioLiquidity,
  PortfolioRisk,
  PortfolioSummary,
  Pricepoint,
  RatingsResponse,
  User,
} from "@/lib/types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

const TOKEN_KEY = "risklens_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
}

function buildUrl(
  path: string,
  query?: RequestOptions["query"]
): string {
  const url = new URL(`${API_URL}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
  }
  return url.toString();
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, query, auth = true } = options;
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Unable to reach the RiskLens API. Is the backend running?",
      0
    );
  }

  if (res.status === 204) return undefined as T;

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : typeof data === "string"
        ? data
        : null) || `Request failed (${res.status})`;
    throw new ApiError(detail, res.status);
  }

  return data as T;
}

// ----- Auth -----
export const login = (email: string, password: string) =>
  request<AuthResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });

export const register = (
  email: string,
  password: string,
  full_name: string
) =>
  request<AuthResponse>("/auth/register", {
    method: "POST",
    body: { email, password, full_name },
    auth: false,
  });

export const me = () => request<User>("/auth/me");

// ----- Instruments -----
export const listInstruments = (params: {
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) =>
  request<Paginated<InstrumentSummary>>("/instruments", {
    query: params,
  });

export const getInstrument = (id: string) =>
  request<InstrumentDetail>(`/instruments/${id}`);

export const instrumentCashflows = (id: string) =>
  request<{ items: Cashflow[] }>(`/instruments/${id}/cashflows`);

export const instrumentPrices = (id: string) =>
  request<{ items: Pricepoint[] }>(`/instruments/${id}/prices`);

export const instrumentRatings = (id: string) =>
  request<RatingsResponse>(`/instruments/${id}/ratings`);

export const instrumentLiquidity = (id: string) =>
  request<LiquidityDetail>(`/instruments/${id}/liquidity`);

export const instrumentNews = (id: string) =>
  request<{ items: NewsItem[] }>(`/instruments/${id}/news`);

// ----- Portfolios -----
export const listPortfolios = () =>
  request<{ items: PortfolioSummary[] }>("/portfolios");

export const createPortfolio = (name: string, description?: string) =>
  request<PortfolioSummary>("/portfolios", {
    method: "POST",
    body: { name, description },
  });

export const getPortfolio = (id: string) =>
  request<PortfolioDetail>(`/portfolios/${id}`);

export const getDashboard = (id: string) =>
  request<DashboardKPIs>(`/portfolios/${id}/dashboard`);

export const getPortfolioRisk = (id: string) =>
  request<PortfolioRisk>(`/portfolios/${id}/risk`);

export const getPortfolioCashflows = (id: string) =>
  request<PortfolioCashflows>(`/portfolios/${id}/cashflows`);

export const getPortfolioLiquidity = (id: string) =>
  request<PortfolioLiquidity>(`/portfolios/${id}/liquidity`);

export const addHolding = (id: string, body: AddHoldingRequest) =>
  request<Holding>(`/portfolios/${id}/holdings`, {
    method: "POST",
    body,
  });

export const deleteHolding = (id: string, holdingId: string) =>
  request<void>(`/portfolios/${id}/holdings/${holdingId}`, {
    method: "DELETE",
  });

// ----- Portfolio builder -----
export const generatePortfolio = (body: BuilderRequest) =>
  request<BuilderResult>("/portfolio-builder/generate", {
    method: "POST",
    body,
  });

// ----- Alerts & reports -----
export const listAlerts = (portfolioId?: string) =>
  request<{ items: Alert[] }>("/alerts", {
    query: { portfolio_id: portfolioId },
  });

export function reportUrl(id: string, format: "xlsx" | "pdf"): string {
  return buildUrl(`/reports/portfolio/${id}`, { format });
}
