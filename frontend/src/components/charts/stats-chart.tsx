"use client";

import ReactECharts from "echarts-for-react";
import { AnalyticsOverview } from "@/lib/api";

export function IndustryChart({ data }: { data: AnalyticsOverview["industry_stats"] }) {
  const option = {
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: data.map((d) => d.name),
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: data.map((d) => d.count),
        itemStyle: { color: "#3b82f6", borderRadius: [4, 4, 0, 0] },
      },
    ],
  };
  return <ReactECharts option={option} style={{ height: 280 }} />;
}

export function HotWordChart({ data }: { data: AnalyticsOverview["hot_words"] }) {
  const option = {
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        data: data.slice(0, 10).map((d) => ({ name: d.keyword, value: d.count })),
        label: { fontSize: 11 },
      },
    ],
  };
  return <ReactECharts option={option} style={{ height: 280 }} />;
}

export function TrendChart({ stats }: { stats: AnalyticsOverview["policy_stats"] }) {
  const option = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: ["今日", "本周", "本月", "累计"] },
    yAxis: { type: "value" },
    series: [
      {
        type: "line",
        smooth: true,
        data: [stats.today, stats.this_week, stats.this_month, stats.total],
        areaStyle: { color: "rgba(59,130,246,0.15)" },
        lineStyle: { color: "#3b82f6", width: 2 },
        itemStyle: { color: "#3b82f6" },
      },
    ],
  };
  return <ReactECharts option={option} style={{ height: 240 }} />;
}
