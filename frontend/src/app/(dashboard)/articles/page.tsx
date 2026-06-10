"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, ExternalLink, Filter, Search, Sparkles } from "lucide-react";
import { api, ArticleListItem, ArticleOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";

const LEVEL_LABEL: Record<string, string> = {
  national: "国家级",
  provincial: "省级",
  municipal: "市级",
  school: "校级",
  unknown: "未分类",
};

const CATEGORY_LABEL: Record<string, string> = {
  national: "国家项目",
  provincial: "省级项目",
  research: "科研类",
  teaching_reform: "教改类",
  other: "其他",
};

const POLICY_TYPE_FILTERS = ["政策文件", "通知公告", "项目申报"];

type LevelFilter = "" | "national" | "provincial" | "municipal" | "school";
type AnalysisFilter = "" | "analyzed" | "pending";

export default function ArticlesPage() {
  const [overview, setOverview] = useState<ArticleOverview | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [level, setLevel] = useState<LevelFilter>("");
  const [analysis, setAnalysis] = useState<AnalysisFilter>("");
  const [policyType, setPolicyType] = useState("");
  const [sourceName, setSourceName] = useState("");
  const limit = 15;

  const loadOverview = useCallback(() => {
    api.getArticleOverview().then(setOverview).catch(console.error);
    api.getArticleSources().then((r) => setSources(r.sources)).catch(console.error);
  }, []);

  const loadArticles = useCallback(() => {
    setLoading(true);
    api
      .getArticles({
        skip: page * limit,
        limit,
        policy_level: level || undefined,
        source_name: sourceName || undefined,
        policy_type: policyType || undefined,
        has_analysis: analysis === "analyzed" ? true : analysis === "pending" ? false : undefined,
        q: searchQ || undefined,
      })
      .then((r) => {
        setArticles(r.items);
        setTotal(r.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, level, analysis, policyType, sourceName, searchQ]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    loadArticles();
  }, [loadArticles]);

  const handleSearch = () => {
    setPage(0);
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">政策知识库</h2>
        <p className="mt-1 text-sm text-slate-500">按级别、类型、来源分类浏览；支持单篇 AI 提炼要点</p>
      </div>

      {overview && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
          {[
            { label: "政策总量", value: overview.total, color: "bg-blue-50 text-blue-700" },
            { label: "已 AI 梳理", value: overview.analyzed, color: "bg-emerald-50 text-emerald-700" },
            { label: "待分析", value: overview.pending, color: "bg-amber-50 text-amber-700" },
            { label: "近7日新增", value: overview.recent_7d, color: "bg-violet-50 text-violet-700" },
            {
              label: "国家级",
              value: overview.by_level.national ?? 0,
              color: "bg-slate-50 text-slate-700",
            },
          ].map((s) => (
            <Card key={s.label}>
              <CardContent className={`rounded-xl py-4 text-center ${s.color}`}>
                <p className="text-xs opacity-80">{s.label}</p>
                <p className="text-2xl font-bold">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-6 lg:flex-row">
        <Card className="lg:w-56 shrink-0">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Filter className="h-4 w-4" /> 分类筛选
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="mb-2 text-xs font-medium text-slate-500">政策级别</p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { key: "", label: "全部" },
                  { key: "national", label: "国家级" },
                  { key: "provincial", label: "省级" },
                  { key: "municipal", label: "市级" },
                  { key: "school", label: "校级" },
                ].map((f) => (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => {
                      setLevel(f.key as LevelFilter);
                      setPage(0);
                    }}
                    className={`rounded-full px-2.5 py-1 text-xs ${
                      level === f.key ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {f.label}
                    {overview && f.key && (
                      <span className="ml-1 opacity-70">({overview.by_level[f.key] ?? 0})</span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-slate-500">文档类型</p>
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setPolicyType("");
                    setPage(0);
                  }}
                  className={`rounded-full px-2.5 py-1 text-xs ${
                    !policyType ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  全部
                </button>
                {POLICY_TYPE_FILTERS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => {
                      setPolicyType(t);
                      setPage(0);
                    }}
                    className={`rounded-full px-2.5 py-1 text-xs ${
                      policyType === t ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-slate-500">AI 状态</p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { key: "", label: "全部" },
                  { key: "analyzed", label: "已梳理" },
                  { key: "pending", label: "待分析" },
                ].map((f) => (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => {
                      setAnalysis(f.key as AnalysisFilter);
                      setPage(0);
                    }}
                    className={`rounded-full px-2.5 py-1 text-xs ${
                      analysis === f.key ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-slate-500">来源网站</p>
              <select
                className="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-xs"
                value={sourceName}
                onChange={(e) => {
                  setSourceName(e.target.value);
                  setPage(0);
                }}
              >
                <option value="">全部来源</option>
                {sources.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        <Card className="min-w-0 flex-1">
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 border-b">
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-4 w-4" />
              政策列表
              <span className="text-sm font-normal text-slate-400">共 {total} 篇</span>
            </CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  className="w-48 pl-8 text-sm"
                  placeholder="搜索标题/内容..."
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
              <Button size="sm" variant="secondary" onClick={handleSearch}>
                搜索
              </Button>
            </div>
          </CardHeader>
          <CardContent className="divide-y divide-slate-100 p-0">
            {loading && <p className="px-6 py-8 text-center text-sm text-slate-400">加载中...</p>}
            {!loading &&
              articles.map((a) => (
                <div key={a.id} className="px-6 py-4 hover:bg-slate-50/80">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/articles/${a.id}`}
                        className="font-medium text-slate-900 hover:text-primary-600"
                      >
                        {a.title}
                      </Link>
                      {a.summary_preview && (
                        <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-slate-500">
                          {a.summary_preview}
                        </p>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        <span>{a.source_name || "未知来源"}</span>
                        <span>·</span>
                        <span>{formatDate(a.publish_time || a.created_at)}</span>
                        <Badge label={LEVEL_LABEL[a.policy_level] || a.policy_level} type={a.policy_level} />
                        {a.policy_type && <Badge label={a.policy_type} type="notice" />}
                        {a.project_category && (
                          <Badge label={CATEGORY_LABEL[a.project_category] || a.project_category} type="inactive" />
                        )}
                        {a.has_analysis ? (
                          <Badge label="已梳理" type="policy" />
                        ) : (
                          <Badge label="待 AI 分析" type="inactive" />
                        )}
                      </div>
                      {a.keywords && a.keywords.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {a.keywords.map((kw) => (
                            <span key={kw} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <a
                      href={a.article_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 text-slate-400 hover:text-primary-600"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              ))}
            {!loading && articles.length === 0 && (
              <p className="px-6 py-12 text-center text-sm text-slate-400">暂无匹配的政策</p>
            )}
          </CardContent>
          {total > limit && (
            <div className="flex items-center justify-between border-t px-6 py-3">
              <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                上一页
              </Button>
              <span className="text-sm text-slate-500">
                {page + 1} / {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={(page + 1) * limit >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                下一页
              </Button>
            </div>
          )}
        </Card>
      </div>

      {overview && overview.top_sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-amber-500" />
              来源分布（采集梳理）
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {overview.top_sources.map((s) => (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => {
                    setSourceName(s.name);
                    setPage(0);
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-left text-sm hover:border-primary-300 hover:bg-primary-50"
                >
                  <span className="font-medium text-slate-800">{s.name}</span>
                  <span className="ml-2 text-slate-400">{s.count} 篇</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
