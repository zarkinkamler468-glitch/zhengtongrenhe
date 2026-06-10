"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Radar, TrendingUp, Zap } from "lucide-react";
import { api, AnalyticsOverview, ArticleListItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendChart } from "@/components/charts/stats-chart";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const [stats, setStats] = useState<AnalyticsOverview | null>(null);
  const [articles, setArticles] = useState<ArticleListItem[]>([]);

  useEffect(() => {
    api.getAnalytics().then(setStats).catch(console.error);
    api.getArticles({ limit: 8 }).then((r) => setArticles(r.items)).catch(console.error);
  }, []);

  const cards = stats
    ? [
        { label: "今日新增", value: stats.policy_stats.today, icon: Zap, color: "text-blue-600" },
        { label: "本周新增", value: stats.policy_stats.this_week, icon: TrendingUp, color: "text-green-600" },
        { label: "本月新增", value: stats.policy_stats.this_month, icon: FileText, color: "text-orange-600" },
        { label: "政策总数", value: stats.policy_stats.total, icon: Radar, color: "text-purple-600" },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.label}>
              <CardContent className="flex items-center gap-4 py-5">
                <div className={`rounded-lg bg-slate-50 p-3 ${c.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">{c.label}</p>
                  <p className="text-2xl font-bold">{c.value}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>政策增长趋势</CardTitle>
          </CardHeader>
          <CardContent>
            {stats && <TrendChart stats={stats.policy_stats} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最新政策动态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {articles.map((a) => (
              <Link
                key={a.id}
                href={`/articles/${a.id}`}
                className="block rounded-lg border border-slate-100 p-3 transition hover:border-primary-200 hover:bg-primary-50/30"
              >
                <p className="line-clamp-1 text-sm font-medium text-slate-900">{a.title}</p>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                  <span>{a.source_name || "未知来源"}</span>
                  <span>·</span>
                  <span>{formatDate(a.publish_time || a.created_at)}</span>
                  {a.has_analysis && <Badge label="已解读" type="policy" />}
                </div>
              </Link>
            ))}
            {articles.length === 0 && (
              <p className="text-sm text-slate-400">暂无数据，请先在监测管理中触发采集</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
