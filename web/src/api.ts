const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

// ---------- Types ----------

export interface CompetitorSummary {
  id: string;
  name: string;
  color: string;
  note_count: number;
  total_engagement: number;
  sentiment_positive_rate: number;
}

export interface CompetitorItem {
  id: string;
  name: string;
  color: string;
}

export interface TrendPoint {
  date: string;
  [competitor: string]: string | number;
}

export interface RadarPoint {
  subject: string;
  [competitor: string]: string | number;
}

export interface HotNote {
  id: string;
  title: string;
  competitor: string;
  interactions: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  time: string;
  url?: string;
}

export interface IndustryNote {
  id: string;
  title: string;
  keyword: string;
  engagement: number;
  interactions: string;
  url?: string;
  publish_time: string;
}

export interface ShareItem {
  name: string;
  value: number;
  color: string;
}

export interface SentimentPoint {
  date: string;
  positive_rate: number;
}

export interface WordItem {
  word: string;
  count: number;
}

export interface CompetitorDetail {
  id: string;
  name: string;
  color: string;
  product_features: {
    quota: string[];
    rate: string[];
    threshold: string[];
    features: string[];
  };
  sentiment_trend: SentimentPoint[];
  top_praises: WordItem[];
  top_complaints: WordItem[];
  hot_notes: Array<{
    id: string;
    title: string;
    engagement: number;
    interactions: string;
    url: string;
    publish_time: string;
  }>;
}

// ---------- API calls ----------

export const api = {
  overview: {
    summary: (days = 7) =>
      fetchAPI<{ data: CompetitorSummary[]; days: number }>(`/api/overview/summary?days=${days}`),
    trend: (days = 30) =>
      fetchAPI<{ data: TrendPoint[] }>(`/api/overview/trend?days=${days}`),
    radar: (days = 30) =>
      fetchAPI<{ data: RadarPoint[] }>(`/api/overview/radar?days=${days}`),
    hotNotes: (days = 7) =>
      fetchAPI<{ data: HotNote[] }>(`/api/overview/hot-notes?days=${days}`),
  },
  competitor: {
    list: () =>
      fetchAPI<{ data: CompetitorItem[] }>(`/api/competitor/list`),
    detail: (id: string, days = 30) =>
      fetchAPI<CompetitorDetail>(`/api/competitor/${id}/detail?days=${days}`),
  },
  industry: {
    volume: (days = 30) =>
      fetchAPI<{ data: TrendPoint[] }>(`/api/industry/volume?days=${days}`),
    hotNotes: (limit = 20, days = 7) =>
      fetchAPI<{ data: IndustryNote[] }>(`/api/industry/hot-notes?limit=${limit}&days=${days}`),
    competitorShare: (days = 30) =>
      fetchAPI<{ data: ShareItem[] }>(`/api/industry/competitor-share?days=${days}`),
  },
};
