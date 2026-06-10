"use client";

import { useEffect, useState } from "react";
import { api, AnalyticsOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IndustryChart, HotWordChart } from "@/components/charts/stats-chart";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);

  useEffect(() => {
    api.getAnalytics().then(setData).catch(console.error);
  }, []);

  if (!data) return <p className="text-slate-500">加载中...</p>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: "今日新增", value: data.policy_stats.today },
          { label: "本周新增", value: data.policy_stats.this_week },
          { label: "本月新增", value: data.policy_stats.this_month },
          { label: "政策总数", value: data.policy_stats.total },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="py-5 text-center">
              <p className="text-sm text-slate-500">{s.label}</p>
              <p className="mt-1 text-3xl font-bold text-primary-700">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>行业政策分布</CardTitle>
          </CardHeader>
          <CardContent>
            <IndustryChart data={data.industry_stats} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>热词分析</CardTitle>
          </CardHeader>
          <CardContent>
            {data.hot_words.length > 0 ? (
              <HotWordChart data={data.hot_words} />
            ) : (
              <p className="py-20 text-center text-sm text-slate-400">暂无热词数据，请先采集并分析政策</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
