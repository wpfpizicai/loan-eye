import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  BarChart3,
  PieChart,
  Search,
  Download,
  Plus,
  TrendingUp,
  TrendingDown,
  MessageSquare,
  Heart,
  Smile,
  Users,
  ExternalLink,
  Eye,
  ChevronRight,
  Circle,
  Loader2,
} from 'lucide-react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, AreaChart, Area, PieChart as RePieChart, Pie, Cell,
} from 'recharts';
import { cn } from './lib/utils';
import { ViewType, MetricCardProps, NoteData } from './types';
import {
  api,
  CompetitorSummary,
  CompetitorItem,
  CompetitorDetail,
  TrendPoint,
  RadarPoint,
  HotNote,
  IndustryNote,
  ShareItem,
} from './api';

// ---------- Helpers ----------

function xhsLink(url: string | undefined, title: string): string {
  if (url && url.includes('xsec_token')) return url;
  return `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(title)}&source=web_search_result_notes`;
}

// ---------- Shared Components ----------

const MetricCard = ({ title, value, change, trend, icon, iconBgColor }: MetricCardProps) => (
  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
    <div className="flex justify-between items-start mb-4">
      <span className="text-slate-500 text-sm font-medium">{title}</span>
      <div className={cn('p-2 rounded-lg', iconBgColor)}>{icon}</div>
    </div>
    <div className="flex items-end gap-2">
      <span className="text-2xl font-bold text-slate-900">{value}</span>
      {change && (
        <span className={cn(
          'text-sm font-semibold flex items-center mb-1',
          trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-slate-400',
        )}>
          {trend === 'up' && <TrendingUp className="w-3 h-3 mr-1" />}
          {trend === 'down' && <TrendingDown className="w-3 h-3 mr-1" />}
          {change}
        </span>
      )}
    </div>
  </div>
);

const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-20">
    <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
  </div>
);

const ErrorMsg = ({ msg }: { msg: string }) => (
  <div className="flex items-center justify-center py-20 text-slate-400 text-sm">{msg}</div>
);

function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fn()
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setError(String(e.message)); setLoading(false); } });
    return () => { cancelled = true; };
  }, deps);

  return { data, loading, error };
}

// ---------- Overview View ----------

function OverviewView({ days }: { days: number }) {
  const { data: summaryData, loading: l1 } = useAsync(() => api.overview.summary(days), [days]);
  const { data: trendData, loading: l2 } = useAsync(() => api.overview.trend(days), [days]);
  const { data: radarData, loading: l3 } = useAsync(() => api.overview.radar(days), [days]);
  const { data: hotNotesData, loading: l4 } = useAsync(() => api.overview.hotNotes(days), [days]);

  if (l1 || l2 || l3 || l4) return <LoadingSpinner />;

  const competitors: CompetitorSummary[] = summaryData?.data ?? [];
  const totalNotes = competitors.reduce((s, c) => s + c.note_count, 0);
  const totalEngagement = competitors.reduce((s, c) => s + c.total_engagement, 0);
  const avgPositive = competitors.length
    ? competitors.reduce((s, c) => s + c.sentiment_positive_rate, 0) / competitors.length
    : 0;

  const rankingData = [...competitors]
    .sort((a, b) => b.total_engagement - a.total_engagement)
    .map((c) => ({ name: c.name, value: c.total_engagement, color: c.color }));

  const trend: TrendPoint[] = trendData?.data ?? [];
  const radar: RadarPoint[] = radarData?.data ?? [];
  const hotNotes: HotNote[] = hotNotesData?.data ?? [];

  // dynamic line colors per competitor
  const compColors = Object.fromEntries(competitors.map((c) => [c.name, c.color]));
  const compNames = competitors.map((c) => c.name);

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">小红书竞品监控仪表盘</h1>
          <p className="text-slate-500 text-sm mt-1">实时追踪金融产品社交媒体表现与用户心智份额</p>
        </div>
        <div className="flex gap-3">
          <button disabled className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed">
            <Download className="w-4 h-4" /> 导出报告
          </button>
          <button disabled className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium opacity-50 cursor-not-allowed">
            <Plus className="w-4 h-4" /> 新增竞品
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="笔记总数" value={totalNotes.toLocaleString()}
          icon={<MessageSquare className="w-5 h-5" />} iconBgColor="bg-blue-50 text-blue-600"
        />
        <MetricCard
          title="总互动量" value={totalEngagement >= 1000 ? `${(totalEngagement / 1000).toFixed(1)}k` : String(totalEngagement)}
          icon={<Heart className="w-5 h-5" />} iconBgColor="bg-orange-50 text-orange-600"
        />
        <MetricCard
          title="平均正向情绪" value={`${(avgPositive * 100).toFixed(1)}%`}
          icon={<Smile className="w-5 h-5" />} iconBgColor="bg-green-50 text-green-600"
        />
        <MetricCard
          title="活跃竞品数" value={String(competitors.length)} trend="neutral" change="持平"
          icon={<Users className="w-5 h-5" />} iconBgColor="bg-slate-50 text-slate-600"
        />
      </div>

      {/* Radar + Ranking */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-6">竞品能力雷达图</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radar}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#64748b' }} />
                {compNames.map((name) => (
                  <Radar
                    key={name} name={name} dataKey={name}
                    stroke={compColors[name]} fill={compColors[name]} fillOpacity={0.3}
                  />
                ))}
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex flex-wrap gap-3 justify-center">
            {competitors.map((c) => (
              <div key={c.id} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: c.color }} />
                <span className="text-xs text-slate-600">{c.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-900">互动量排行榜 (总计)</h3>
            <span className="text-xs text-slate-400">单位: 互动数</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={rankingData} margin={{ left: 20, right: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 12, fill: '#475569' }} />
                <Tooltip cursor={{ fill: 'transparent' }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={32}>
                  {rankingData.map((entry, i) => (
                    <Cell key={`cell-${i}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-lg font-bold text-slate-900">每日声量趋势 (发文数)</h3>
          <div className="flex items-center gap-4">
            {compNames.map((name) => (
              <div key={name} className="flex items-center gap-2">
                <div className="w-3 h-0.5" style={{ backgroundColor: compColors[name] }} />
                <span className="text-xs text-slate-500">{name}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip />
              {compNames.map((name, i) => (
                <Line
                  key={name} type="monotone" dataKey={name}
                  stroke={compColors[name]} strokeWidth={i === 0 ? 3 : 2}
                  strokeDasharray={i > 0 ? '5 5' : undefined} dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Hot Notes Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-lg font-bold text-slate-900">实时爆款笔记 (Top 5)</h3>
          <button className="text-blue-600 text-sm font-semibold hover:underline">查看全部</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-500 text-xs font-bold uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4">笔记标题</th>
                <th className="px-6 py-4">竞品名称</th>
                <th className="px-6 py-4">总互动量</th>
                <th className="px-6 py-4">情感倾向</th>
                <th className="px-6 py-4">发布时间</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {hotNotes.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-400 text-sm">暂无数据</td></tr>
              ) : hotNotes.map((note, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-medium max-w-xs truncate">
                    <a href={xhsLink(note.url, note.title)} target="_blank" rel="noreferrer" className="text-slate-900 hover:text-blue-600 hover:underline transition-colors">{note.title}</a>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className="px-2 py-1 text-[10px] font-bold rounded"
                      style={{
                        backgroundColor: compColors[note.competitor] ? `${compColors[note.competitor]}18` : '#f1f5f9',
                        color: compColors[note.competitor] ?? '#64748b',
                      }}
                    >
                      {note.competitor}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{note.interactions}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      'flex items-center gap-1 font-medium text-xs',
                      note.sentiment === 'positive' ? 'text-green-600' :
                      note.sentiment === 'negative' ? 'text-red-600' : 'text-slate-600',
                    )}>
                      <Circle className="w-2 h-2 fill-current" />
                      {note.sentiment === 'positive' ? '正向' : note.sentiment === 'negative' ? '负向' : '中性'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-xs">{note.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---------- Details View ----------

function DetailsView({ days }: { days: number }) {
  const { data: listData, loading: listLoading } = useAsync(() => api.competitor.list(), []);
  const competitors: CompetitorItem[] = listData?.data ?? [];
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Auto-select first competitor
  useEffect(() => {
    if (competitors.length > 0 && !selectedId) {
      setSelectedId(competitors[0].id);
    }
  }, [competitors]);

  const { data: detail, loading: detailLoading, error: detailError } = useAsync(
    () => selectedId ? api.competitor.detail(selectedId, days) : Promise.resolve(null),
    [selectedId, days],
  );

  if (listLoading) return <LoadingSpinner />;

  const sentimentTrend = (detail?.sentiment_trend ?? []).map((p) => ({
    date: p.date,
    positive: +(p.positive_rate * 100).toFixed(1),
    negative: +((1 - p.positive_rate) * 100).toFixed(1),
  }));

  const praises = detail?.top_praises ?? [];
  const complaints = detail?.top_complaints ?? [];
  const features = detail?.product_features ?? { quota: [], rate: [], threshold: [], features: [] };
  const hotNotes = detail?.hot_notes ?? [];

  return (
    <div className="space-y-8">
      {/* Competitor Tabs */}
      <div className="mb-8">
        <div className="flex border-b border-slate-200 gap-8">
          {competitors.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedId(c.id)}
              className={cn(
                'flex flex-col items-center justify-center pb-3 px-4 transition-all font-medium',
                selectedId === c.id
                  ? 'border-b-2 border-blue-600 text-blue-600 font-bold'
                  : 'text-slate-500 hover:text-slate-800',
              )}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {detailLoading && <LoadingSpinner />}
      {detailError && <ErrorMsg msg={`加载失败: ${detailError}`} />}

      {!detailLoading && !detailError && detail && (
        <div className="grid grid-cols-12 gap-6">
          {/* Product Features */}
          <section className="col-span-12 lg:col-span-4 bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-2 mb-6">
              <Smile className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-bold">产品核心能力</h3>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-lg flex justify-between items-center">
                <span className="text-slate-500 text-sm">最高额度 (Quota)</span>
                <span className="text-slate-900 font-bold text-sm">
                  {features.quota.length > 0 ? features.quota[0] : '暂无数据'}
                </span>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg flex justify-between items-center">
                <span className="text-slate-500 text-sm">年化利率 (Interest)</span>
                <span className="text-blue-600 font-bold text-sm">
                  {features.rate.length > 0 ? features.rate[0] : '暂无数据'}
                </span>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg flex flex-col gap-2">
                <span className="text-slate-500 text-sm">准入门槛 (Threshold)</span>
                <span className="text-slate-900 text-sm leading-relaxed">
                  {features.threshold.length > 0 ? features.threshold.join('，') : '暂无数据'}
                </span>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg flex flex-col gap-2">
                <span className="text-slate-500 text-sm">特色功能 (Features)</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {features.features.length > 0
                    ? features.features.map((f, i) => (
                        <span key={i} className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded">{f}</span>
                      ))
                    : <span className="text-sm text-slate-400">暂无数据</span>
                  }
                </div>
              </div>
            </div>
          </section>

          {/* Sentiment Trend */}
          <section className="col-span-12 lg:col-span-8 bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-bold">声量与情感趋势</h3>
              </div>
              <div className="flex gap-4 text-xs">
                <div className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded-full" /> 正面率</div>
                <div className="flex items-center gap-1"><span className="w-3 h-3 bg-red-400 rounded-full" /> 负面率</div>
              </div>
            </div>
            <div className="h-64">
              {sentimentTrend.length === 0 ? (
                <div className="flex items-center justify-center h-full text-slate-400 text-sm">暂无趋势数据</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sentimentTrend}>
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip formatter={(v: number) => `${v}%`} />
                    <Area type="monotone" dataKey="positive" name="正面率" stroke="#1a90ff" fill="#1a90ff" fillOpacity={0.1} strokeWidth={3} />
                    <Area type="monotone" dataKey="negative" name="负面率" stroke="#f87171" fill="#f87171" fillOpacity={0.05} strokeWidth={2} strokeDasharray="5 5" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>

          {/* Word Clouds */}
          <section className="col-span-12 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-md font-bold mb-4 flex items-center gap-2 text-green-600">
                <Smile className="w-4 h-4" /> 好评热词
              </h3>
              <div className="h-40 relative flex flex-wrap items-center justify-center gap-3 overflow-hidden bg-green-50/30 rounded-lg p-4">
                {praises.length === 0
                  ? <span className="text-slate-400 text-sm">暂无数据</span>
                  : praises.map((w, i) => {
                      const sizes = ['text-2xl font-bold', 'text-xl font-medium', 'text-lg', 'text-base', 'text-sm'];
                      const shades = ['text-green-600', 'text-green-500', 'text-green-400', 'text-green-400', 'text-green-400'];
                      return (
                        <span key={i} className={cn(sizes[Math.min(i, 4)], shades[Math.min(i, 4)])}>{w.word}</span>
                      );
                    })
                }
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <h3 className="text-md font-bold mb-4 flex items-center gap-2 text-red-600">
                <MessageSquare className="w-4 h-4" /> 投诉热词
              </h3>
              <div className="h-40 relative flex flex-wrap items-center justify-center gap-3 overflow-hidden bg-red-50/30 rounded-lg p-4">
                {complaints.length === 0
                  ? <span className="text-slate-400 text-sm">暂无数据</span>
                  : complaints.map((w, i) => {
                      const sizes = ['text-2xl font-bold', 'text-xl font-medium', 'text-lg', 'text-base', 'text-sm'];
                      const shades = ['text-red-600', 'text-red-500', 'text-red-400', 'text-red-400', 'text-red-400'];
                      return (
                        <span key={i} className={cn(sizes[Math.min(i, 4)], shades[Math.min(i, 4)])}>{w.word}</span>
                      );
                    })
                }
              </div>
            </div>
          </section>

          {/* Hot Notes Table */}
          <section className="col-span-12 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-bold">爆款笔记监控 (Xiaohongshu)</h3>
              </div>
              <button className="text-sm text-blue-600 font-medium hover:underline">查看更多</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase font-bold">
                  <tr>
                    <th className="px-6 py-4">笔记标题</th>
                    <th className="px-6 py-4">互动量 (总计)</th>
                    <th className="px-6 py-4">发布时间</th>
                    <th className="px-6 py-4">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {hotNotes.length === 0 ? (
                    <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-400 text-sm">暂无爆款笔记</td></tr>
                  ) : hotNotes.map((note, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium line-clamp-1">{note.title}</span>
                      </td>
                      <td className="px-6 py-4 text-sm font-bold text-slate-700">{note.interactions}</td>
                      <td className="px-6 py-4 text-sm text-slate-500">{note.publish_time}</td>
                      <td className="px-6 py-4">
                        {true ? (
                          <a href={xhsLink(note.url, note.title)} target="_blank" rel="noreferrer"
                            className="text-blue-600 hover:text-blue-800 flex items-center gap-1 text-sm font-medium">
                            查看原贴 <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-300 text-sm">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

// ---------- Industry View ----------

function IndustryView({ days }: { days: number }) {
  const { data: volumeData, loading: l1 } = useAsync(() => api.industry.volume(days), [days]);
  const { data: hotNotesData, loading: l2 } = useAsync(() => api.industry.hotNotes(20, days), [days]);
  const { data: shareData, loading: l3 } = useAsync(() => api.industry.competitorShare(days), [days]);

  if (l1 || l2 || l3) return <LoadingSpinner />;

  const trend: any[] = volumeData?.data ?? [];
  const hotNotes: IndustryNote[] = hotNotesData?.data ?? [];
  const rawShare: any[] = shareData?.data ?? [];

  // Convert raw note counts to percentages
  const totalShare = rawShare.reduce((s: number, d: any) => s + d.value, 0) || 1;
  const sovData = rawShare.map((d: any) => ({ ...d, pct: +((d.value / totalShare) * 100).toFixed(1) }));
  const topName = sovData.length > 0 ? sovData.reduce((a: any, b: any) => (a.value > b.value ? a : b)).name : '';

  // Industry aggregate stats from share data
  const totalNotes = rawShare.reduce((s: number, d: any) => s + d.value, 0);

  // Keys for trend chart (industry volume has dynamic keys)
  const trendKeys = trend.length > 0 ? Object.keys(trend[0]).filter((k) => k !== 'date') : [];
  const lineColors = ['#1a90ff', '#34d399', '#fbbf24', '#f87171', '#a78bfa'];

  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-slate-500 text-sm mb-1">竞品笔记总数 (近{days}天)</p>
          <h3 className="text-2xl font-bold">{totalNotes.toLocaleString()}</h3>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-slate-500 text-sm mb-1">监控竞品数</p>
          <h3 className="text-2xl font-bold">{sovData.length}</h3>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-slate-500 text-sm mb-1">行业热门笔记</p>
          <h3 className="text-2xl font-bold">{hotNotes.length}</h3>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-slate-500 text-sm mb-1">声量第一竞品</p>
          <h3 className="text-2xl font-bold truncate">{topName || '—'}</h3>
        </div>
      </div>

      {/* Volume Trend */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-bold text-lg">行业关键词声量趋势</h3>
          <div className="flex gap-4 text-xs text-slate-500">
            {trendKeys.map((k, i) => (
              <span key={k} className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: lineColors[i % lineColors.length] }} />
                {k}
              </span>
            ))}
          </div>
        </div>
        <div className="h-72">
          {trend.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-400 text-sm">暂无趋势数据</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip />
                {trendKeys.map((k, i) => (
                  <Area
                    key={k} type="monotone" dataKey={k}
                    stroke={lineColors[i % lineColors.length]}
                    fill={lineColors[i % lineColors.length]}
                    fillOpacity={0.1} strokeWidth={2}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* SOV Pie Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="font-bold text-lg mb-8">竞品声量占有率 (SOV)</h3>
        {sovData.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-slate-400 text-sm">暂无数据</div>
        ) : (
          <div className="flex flex-col md:flex-row items-center justify-around gap-8">
            <div className="relative w-56 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie
                    data={sovData} cx="50%" cy="50%"
                    innerRadius={60} outerRadius={80}
                    paddingAngle={5} dataKey="value"
                  >
                    {sovData.map((entry: any, i: number) => (
                      <Cell key={`cell-${i}`} fill={entry.color} />
                    ))}
                  </Pie>
                </RePieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-[10px] text-slate-500">排名第1</span>
                <span className="text-base font-bold">{topName}</span>
              </div>
            </div>
            <div className="w-full max-w-md space-y-4">
              {sovData.map((item: any, idx: number) => (
                <div key={idx} className="flex justify-between items-center text-sm p-2 hover:bg-slate-50 rounded transition-colors">
                  <span className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    {item.name}
                  </span>
                  <span className="font-bold">{item.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Industry Hot Notes */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex justify-between items-center">
          <h3 className="font-bold text-lg">行业热门笔记 (Top 20)</h3>
          <button className="text-blue-600 text-sm font-medium flex items-center gap-1 hover:underline">
            查看全部 <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase font-bold">
              <tr>
                <th className="px-6 py-4">排名</th>
                <th className="px-6 py-4">笔记标题</th>
                <th className="px-6 py-4">关键词</th>
                <th className="px-6 py-4">互动量</th>
                <th className="px-6 py-4">发布日期</th>
                <th className="px-6 py-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {hotNotes.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-400 text-sm">暂无数据</td></tr>
              ) : hotNotes.map((item, idx) => {
                const rankColors = ['bg-amber-100 text-amber-600', 'bg-slate-200 text-slate-600', 'bg-orange-100 text-orange-600'];
                const rankColor = rankColors[idx] ?? '';
                return (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      {rankColor ? (
                        <span className={cn('w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold', rankColor)}>
                          {idx + 1}
                        </span>
                      ) : (
                        <span className="w-6 h-6 flex items-center justify-center text-xs text-slate-400 pl-2">{idx + 1}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium max-w-xs truncate">{item.title}</td>
                    <td className="px-6 py-4 text-xs">
                      <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded">{item.keyword}</span>
                    </td>
                    <td className="px-6 py-4 text-sm font-bold text-blue-600">{item.interactions}</td>
                    <td className="px-6 py-4 text-sm text-slate-500">{item.publish_time}</td>
                    <td className="px-6 py-4 text-right">
                      <a href={xhsLink(item.url, item.title)} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-blue-600 transition-colors">
                        <Eye className="w-4 h-4" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---------- Main App ----------

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [days, setDays] = useState(7);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white p-1.5 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">loan-eye</h2>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            {(['overview', 'details', 'industry'] as ViewType[]).map((v) => (
              <button
                key={v}
                onClick={() => setCurrentView(v)}
                className={cn(
                  'text-sm font-medium transition-colors pb-1 border-b-2',
                  currentView === v ? 'text-blue-600 border-blue-600 font-semibold' : 'text-slate-500 hover:text-blue-600 border-transparent',
                )}
              >
                {v === 'overview' ? '竞品总览' : v === 'details' ? '竞品详情' : '行业声量'}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-6">
          {/* Time Range Toggle */}
          <div className="hidden lg:flex items-center bg-slate-100 rounded-lg p-1">
            {[{ label: '近7天', value: 7 }, { label: '近30天', value: 30 }].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDays(opt.value)}
                className={cn(
                  'px-4 py-1.5 text-xs font-medium rounded-md transition-all',
                  days === opt.value ? 'bg-white shadow-sm text-slate-900 font-semibold' : 'text-slate-500 hover:text-slate-700',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="搜索竞品或功能..."
              className="bg-slate-100 border-none rounded-lg py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-600/20 w-48 lg:w-64"
            />
          </div>

          <div className="flex items-center gap-3 border-l border-slate-200 pl-6">
            <div className="flex flex-col items-end">
              <span className="text-xs font-semibold">分析师团队</span>
              <span className="text-[10px] text-slate-400">高级管理员</span>
            </div>
            <div className="w-9 h-9 rounded-full bg-slate-200 overflow-hidden ring-2 ring-blue-600/10">
              <img alt="Profile" className="w-full h-full object-cover"
                src="https://picsum.photos/seed/user1/100/100" referrerPolicy="no-referrer" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto w-full p-6">
        {currentView === 'overview' && <OverviewView days={days} />}
        {currentView === 'details' && <DetailsView days={days} />}
        {currentView === 'industry' && <IndustryView days={days} />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12 p-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-slate-500">数据实时更新中</span>
            </div>
            <span className="text-xs text-slate-300">|</span>
            <span className="text-xs text-slate-500 font-medium">
              最后同步时间: {new Date().toLocaleString('zh-CN')}
            </span>
          </div>
          <p className="text-[10px] text-slate-400">© 2024 loan-eye Competitor Monitoring Platform. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
