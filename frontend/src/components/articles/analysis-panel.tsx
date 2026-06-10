"use client";

import { useLayoutEffect, useRef } from "react";
import type { ElementType } from "react";
import gsap from "gsap";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  Calendar,
  CircleDollarSign,
  FileText,
  GraduationCap,
  Lightbulb,
  ListChecks,
  Sparkles,
  Tag,
  Target,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { staggerReveal } from "@/lib/gsap-motion";

type AnalysisData = NonNullable<{
  summary_100: string | null;
  summary_300: string | null;
  summary_page: string | null;
  tags: Record<string, string> | null;
  keywords: string[] | null;
  key_info: Record<string, string | null> | null;
  analysis: Record<string, string> | null;
}>;

const TAG_LABEL: Record<string, string> = {
  policy_type: "文档类型",
  industry: "行业领域",
  level: "发布级别",
  urgency: "紧急程度",
};

const KEY_INFO_META: Record<
  string,
  { label: string; icon: ElementType; highlight?: boolean; tone?: string }
> = {
  project_name: { label: "项目名称", icon: FileText, tone: "border-blue-200 bg-blue-50/80" },
  publish_time: { label: "发布时间", icon: Calendar, tone: "border-slate-200 bg-slate-50" },
  apply_start: { label: "申报开始", icon: Calendar, highlight: true, tone: "border-emerald-200 bg-emerald-50/90" },
  deadline: { label: "截止时间", icon: AlertTriangle, highlight: true, tone: "border-amber-300 bg-amber-50 ring-1 ring-amber-200/80" },
  funding_amount: { label: "资助金额", icon: CircleDollarSign, highlight: true, tone: "border-violet-200 bg-violet-50/90" },
  target_audience: { label: "申报对象", icon: Users, tone: "border-sky-200 bg-sky-50/80" },
  contact: { label: "联系方式", icon: Target, tone: "border-slate-200 bg-slate-50" },
  contact_person: { label: "联系人", icon: Users, tone: "border-slate-200 bg-slate-50" },
};

const SECTION_META: Record<string, { label: string; icon: ElementType; accent: string }> = {
  background: { label: "政策背景", icon: BookOpen, accent: "border-l-blue-500 bg-blue-50/40" },
  reason: { label: "出台原因", icon: Lightbulb, accent: "border-l-amber-500 bg-amber-50/40" },
  core_content: { label: "核心内容", icon: FileText, accent: "border-l-primary-500 bg-primary-50/50" },
  key_tasks: { label: "重点任务", icon: ListChecks, accent: "border-l-emerald-500 bg-emerald-50/40" },
  impact_university: { label: "对高校影响", icon: GraduationCap, accent: "border-l-indigo-500 bg-indigo-50/40" },
  impact_enterprise: { label: "对企业影响", icon: Building2, accent: "border-l-violet-500 bg-violet-50/40" },
  application_advice: { label: "申报建议", icon: Target, accent: "border-l-rose-500 bg-rose-50/50" },
};

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** 将关键词在文本中高亮 */
function HighlightText({ text, keywords }: { text: string; keywords: string[] }) {
  if (!keywords.length) {
    return <span>{text}</span>;
  }
  const sorted = [...keywords].filter(Boolean).sort((a, b) => b.length - a.length);
  const pattern = sorted.map(escapeRegExp).join("|");
  if (!pattern) return <span>{text}</span>;

  const parts = text.split(new RegExp(`(${pattern})`, "gi"));
  return (
    <span>
      {parts.map((part, i) => {
        const isHit = sorted.some((kw) => part.toLowerCase() === kw.toLowerCase());
        return isHit ? (
          <mark
            key={`${part}-${i}`}
            className="rounded px-0.5 font-semibold text-amber-900"
            style={{ background: "linear-gradient(180deg, transparent 55%, #fde68a 55%)" }}
          >
            {part}
          </mark>
        ) : (
          <span key={`${part}-${i}`}>{part}</span>
        );
      })}
    </span>
  );
}

function urgencyStyle(urgency?: string) {
  if (!urgency) return null;
  if (urgency.includes("高")) {
    return {
      banner: "border-red-200 bg-gradient-to-r from-red-50 to-orange-50 text-red-800",
      badge: "bg-red-100 text-red-700 ring-red-200",
      label: "高优先级",
    };
  }
  if (urgency.includes("中")) {
    return {
      banner: "border-amber-200 bg-gradient-to-r from-amber-50 to-yellow-50 text-amber-900",
      badge: "bg-amber-100 text-amber-800 ring-amber-200",
      label: "中优先级",
    };
  }
  return {
    banner: "border-slate-200 bg-slate-50 text-slate-700",
    badge: "bg-slate-100 text-slate-600 ring-slate-200",
    label: "常规关注",
  };
}

function tagTone(key: string, value: string) {
  if (key === "urgency" && value.includes("高")) return "bg-red-100 text-red-700";
  if (key === "policy_type" && value.includes("申报")) return "bg-violet-100 text-violet-700";
  if (key === "level" && value.includes("国家")) return "bg-blue-100 text-blue-700";
  if (key === "industry") return "bg-emerald-100 text-emerald-700";
  return "bg-slate-100 text-slate-700";
}

export function AnalysisPanel({ analysis }: { analysis: AnalysisData }) {
  const rootRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      staggerReveal(rootRef.current, "[data-reveal]", { y: 22, stagger: 0.1, duration: 0.5 });
    }, rootRef);
    return () => ctx.revert();
  }, [analysis]);

  const keywords = analysis.keywords ?? [];
  const urgency = analysis.tags?.urgency;
  const urgencyUi = urgencyStyle(urgency);

  const highlightFields = Object.entries(analysis.key_info ?? {}).filter(
    ([k, v]) => v && KEY_INFO_META[k]?.highlight
  );
  const normalFields = Object.entries(analysis.key_info ?? {}).filter(
    ([k, v]) => v && !KEY_INFO_META[k]?.highlight
  );

  return (
    <div ref={rootRef} className="space-y-5">
      {/* 顶部重点提示条 */}
      {urgencyUi && (
        <div data-reveal className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${urgencyUi.banner}`}>
          <AlertTriangle className="h-5 w-5 shrink-0 opacity-80" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">{urgencyUi.label}</p>
            <p className="text-xs opacity-80">紧急程度：{urgency}</p>
          </div>
          {highlightFields.find(([k]) => k === "deadline")?.[1] && (
            <div className="shrink-0 rounded-lg bg-white/70 px-3 py-1.5 text-center shadow-sm">
              <p className="text-[10px] uppercase tracking-wide text-amber-700">截止</p>
              <p className="text-sm font-bold text-amber-900">
                {highlightFields.find(([k]) => k === "deadline")?.[1]}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 要点提炼 Hero */}
      <Card data-reveal className="overflow-hidden border-0 shadow-md ring-1 ring-primary-200/60">
        <div className="bg-gradient-to-br from-primary-600 via-primary-500 to-indigo-500 px-6 py-5 text-white">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold">AI 要点提炼</h3>
              <p className="text-xs text-white/80">智能摘要 · 关键词高亮 · 重点信息</p>
            </div>
          </div>
        </div>
        <CardContent className="space-y-4 bg-gradient-to-b from-primary-50/30 to-white p-6">
          {analysis.summary_100 && (
            <div className="relative rounded-xl border border-primary-100 bg-white p-5 shadow-sm">
              <span className="absolute -top-2.5 left-4 rounded-full bg-primary-600 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                一句话读懂
              </span>
              <p className="mt-1 text-base font-medium leading-relaxed text-slate-800">
                <HighlightText text={analysis.summary_100} keywords={keywords} />
              </p>
            </div>
          )}
          {analysis.summary_300 && (
            <div className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <FileText className="h-3.5 w-3.5" /> 核心摘要
              </p>
              <p className="text-sm leading-7 text-slate-700">
                <HighlightText text={analysis.summary_300} keywords={keywords} />
              </p>
            </div>
          )}
          {keywords.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-500">关键词</p>
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw, idx) => (
                  <span
                    key={kw}
                    className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ring-1 ${
                      idx < 3
                        ? "bg-amber-100 text-amber-900 ring-amber-200"
                        : "bg-slate-100 text-slate-600 ring-slate-200"
                    }`}
                  >
                    {idx < 3 && <span className="text-[10px]">★</span>}
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 智能标签 */}
      {analysis.tags && Object.keys(analysis.tags).length > 0 && (
        <Card data-reveal>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Tag className="h-4 w-4 text-primary-600" />
              智能分类
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(analysis.tags).map(([k, v]) => (
                <span
                  key={k}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${tagTone(k, v)}`}
                >
                  <span className="text-xs opacity-70">{TAG_LABEL[k] || k}</span>
                  <span className="font-semibold">{v}</span>
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 关键信息 - 重点字段突出 */}
      {highlightFields.length > 0 && (
        <Card data-reveal className="border-amber-100">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base text-amber-900">
              <AlertTriangle className="h-4 w-4" />
              重点提示
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {highlightFields.map(([k, v]) => {
                const meta = KEY_INFO_META[k];
                const Icon = meta?.icon ?? FileText;
                return (
                  <div
                    key={k}
                    className={`rounded-xl border-2 p-4 ${meta?.tone ?? "border-slate-200 bg-slate-50"}`}
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <Icon className="h-4 w-4 opacity-70" />
                      <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                        {meta?.label || k}
                      </span>
                      {k === "deadline" && (
                        <span className="ml-auto rounded bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                          重要
                        </span>
                      )}
                      {k === "funding_amount" && (
                        <span className="ml-auto rounded bg-violet-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                          资金
                        </span>
                      )}
                    </div>
                    <p className="text-base font-bold leading-snug text-slate-900">{v}</p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {normalFields.length > 0 && (
        <Card data-reveal>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">关键信息</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {normalFields.map(([k, v]) => {
                const meta = KEY_INFO_META[k];
                const Icon = meta?.icon ?? FileText;
                return (
                  <div key={k} className={`rounded-xl border p-4 ${meta?.tone ?? "border-slate-100 bg-slate-50/50"}`}>
                    <dt className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Icon className="h-3.5 w-3.5" />
                      {meta?.label || k}
                    </dt>
                    <dd className="mt-1.5 text-sm font-medium text-slate-800">{v}</dd>
                  </div>
                );
              })}
            </dl>
          </CardContent>
        </Card>
      )}

      {/* 深度解读 */}
      {analysis.analysis && Object.values(analysis.analysis).some(Boolean) && (
        <Card data-reveal>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-4 w-4 text-indigo-600" />
              深度政策解读
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(SECTION_META).map(([key, meta]) => {
              const content = analysis.analysis?.[key];
              if (!content) return null;
              const Icon = meta.icon;
              const isAdvice = key === "application_advice";
              return (
                <div
                  key={key}
                  className={`rounded-xl border-l-4 p-4 ${meta.accent} ${isAdvice ? "ring-1 ring-rose-200" : ""}`}
                >
                  <h4 className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-800">
                    <Icon className="h-4 w-4 shrink-0 opacity-70" />
                    {meta.label}
                    {isAdvice && (
                      <Badge label="建议关注" type="policy" />
                    )}
                  </h4>
                  <p className="text-sm leading-7 text-slate-700">
                    <HighlightText text={content} keywords={keywords} />
                  </p>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* 一页纸 */}
      {analysis.summary_page && (
        <Card data-reveal className="bg-slate-50/50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4" />
              一页纸详读
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm leading-7 text-slate-700 shadow-inner">
              <HighlightText text={analysis.summary_page} keywords={keywords} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
