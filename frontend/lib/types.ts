// Shared API types for the RiskLens frontend. These mirror the shapes
// described in docs/API.md. Fields that the backend may omit are optional.

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface InstrumentSummary {
  id: string;
  isin: string;
  name: string;
  category: string;
  issuer_name: string;
  sector: string | null;
  coupon_rate: number | null;
  maturity_date: string | null;
  clean_price: number | null;
  ytm: number | null;
  modified_duration: number | null;
  rating: string | null;
  rating_agency: string | null;
  liquidity_score: number | null;
  liquidity_class: string | null;
  is_government: boolean;
  data_status: string;
}

export interface InstrumentAnalytics {
  ytm?: number | null;
  current_yield?: number | null;
  ytc?: number | null;
  macaulay_duration?: number | null;
  modified_duration?: number | null;
  convexity?: number | null;
  dv01?: number | null;
  accrued_interest?: number | null;
  clean_price?: number | null;
  dirty_price?: number | null;
  [key: string]: number | null | undefined;
}

export interface InstrumentDetail extends InstrumentSummary {
  issue_date: string | null;
  face_value: number | null;
  coupon_frequency: number | null;
  day_count: string | null;
  callable: boolean | null;
  puttable: boolean | null;
  secured: boolean | null;
  seniority: string | null;
  accrued_interest: number | null;
  dirty_price: number | null;
  current_yield: number | null;
  ytc: number | null;
  convexity: number | null;
  dv01: number | null;
  analytics: InstrumentAnalytics | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Cashflow {
  pay_date: string;
  amount: number;
  kind: string;
}

export interface Pricepoint {
  price_date: string;
  clean_price: number;
  source: string;
}

export interface RatingEntry {
  agency?: string;
  rating?: string;
  outlook?: string | null;
  rated_at?: string;
  action?: string;
  [key: string]: unknown;
}

export interface RatingsResponse {
  current: RatingEntry | null;
  history: RatingEntry[];
}

export interface LiquidityComponent {
  name: string;
  value: number | null;
  weight?: number | null;
}

export interface LiquidityDetail {
  liquidity_score: number | null;
  liquidity_class: string | null;
  components?: LiquidityComponent[];
  classification?: string | null;
  disclaimer?: string | null;
  [key: string]: unknown;
}

export interface NewsItem {
  id: string;
  headline: string;
  source: string;
  published_at: string;
  category: string;
  summary: string;
  risk_impact: string;
  relevance: number | string | null;
  issuer_name: string | null;
  data_status: string;
}

export interface PortfolioSummary {
  id: string;
  name: string;
  description?: string | null;
  total_value?: number | null;
  holdings_count?: number | null;
  data_status?: string;
  [key: string]: unknown;
}

export interface HoldingAnalytics {
  ytm?: number | null;
  modified_duration?: number | null;
  dv01?: number | null;
  market_value?: number | null;
  gain_loss?: number | null;
  [key: string]: number | null | undefined;
}

export interface Holding {
  id: string;
  instrument_id: string;
  instrument_name?: string | null;
  name?: string | null;
  category?: string | null;
  issuer_name?: string | null;
  quantity: number;
  buy_price: number;
  buy_date: string;
  clean_price?: number | null;
  market_value?: number | null;
  weight?: number | null;
  gain_loss?: number | null;
  rating?: string | null;
  analytics?: HoldingAnalytics | null;
  [key: string]: unknown;
}

export interface PortfolioDetail extends PortfolioSummary {
  holdings: Holding[];
}

export interface AllocationSlice {
  label: string;
  value: number;
  weight?: number | null;
}

export interface MaturityBucket {
  label: string;
  value: number;
}

export interface DashboardKPIs {
  total_value: number | null;
  unrealised_gain_loss: number | null;
  gain_loss_pct?: number | null;
  weighted_yield: number | null;
  annual_income: number | null;
  modified_duration: number | null;
  dv01: number | null;
  allocations_by_category?: AllocationSlice[];
  rating_distribution?: AllocationSlice[];
  maturity_ladder?: MaturityBucket[];
  issuer_concentration?: { issuer: string; weight: number }[];
  low_liquidity_holdings?: { name: string; liquidity_class: string }[];
  downgrade_alerts?: { message: string; severity?: string }[];
  [key: string]: unknown;
}

export interface ScenarioResult {
  name: string;
  description: string;
  pnl: number;
  pnl_pct: number;
  disclaimer?: string;
}

export interface PortfolioRisk {
  duration: number | null;
  convexity: number | null;
  dv01: number | null;
  rating_distribution?: AllocationSlice[];
  issuer_concentration?: { issuer: string; weight: number }[];
  stress: ScenarioResult[];
  [key: string]: unknown;
}

export interface CashflowCalendarEntry {
  month: string;
  coupon: number;
  principal: number;
  total: number;
}

export interface PortfolioCashflows {
  calendar: CashflowCalendarEntry[];
  upcoming: Cashflow[];
}

export interface LiquidityBuckets {
  high: number;
  moderate: number;
  low: number;
  insufficient: number;
}

export interface PortfolioLiquidity {
  buckets: LiquidityBuckets;
  est_liquidation_days: number | null;
  illiquid_holdings: { name: string; liquidity_class?: string; weight?: number }[];
  disclaimer?: string | null;
}

export type BuilderObjective =
  | "max_yield"
  | "max_income"
  | "min_duration"
  | "max_liquidity";

export interface BuilderConstraints {
  max_issuer_weight?: number;
  max_sector_weight?: number;
  min_government_weight?: number;
  max_low_rated_weight?: number;
  min_liquidity_weight?: number;
  max_duration?: number;
  max_maturity_years?: number;
  max_weight_per_instrument?: number;
  min_instruments?: number;
}

export interface BuilderRequest {
  amount: number;
  objective: BuilderObjective;
  constraints: BuilderConstraints;
  universe: string[];
}

export interface BuilderAllocation {
  instrument_id: string;
  name: string;
  issuer: string;
  category: string;
  weight: number;
  amount: number;
  ytm: number | null;
  modified_duration: number | null;
  rating: string | null;
  liquidity_class: string | null;
  rationale: string;
}

export interface BuilderResult {
  feasible: boolean;
  objective: string;
  expected_yield: number | null;
  expected_duration: number | null;
  allocations: BuilderAllocation[];
  infeasible_reasons: string[];
  methodology: string;
}

export interface Alert {
  id: string;
  trigger: string;
  severity: string;
  instrument_id: string | null;
  portfolio_id: string | null;
  exposure: number | null;
  message: string;
  created_at: string;
  status: string;
  source: string;
}

export interface AddHoldingRequest {
  instrument_id: string;
  quantity: number;
  buy_price: number;
  buy_date: string;
}
