"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { api, ArticleDetail } from "@/lib/api";
import { AnalysisPanel } from "@/components/articles/analysis-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

const LEVEL_LABEL: Record<string, string> = {
  national: "国家级",
  provincial: "省级",
  municipal: "市级",
  school: "校级",
  unknown: "未分类",
};

export default function ArticleDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const validId = Number.isFinite(id) && id > 0;
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const load = useCallback(() => {
    if (!validId) {
      setLoading(false);
      setLoadError("无效的文章 ID");
      return;
    }
    setLoading(true);
    setLoadError(null);
    api
      .getArticle(id)
      .then((data) => {
        setArticle(data);
        setLoadError(null);
      })
      .catch((e) => {
        setArticle(null);
        setLoadError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => setLoading(false));
  }, [id, validId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAnalyze = async (force = false) => {
    if (!validId) return;
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setAnalyzing(true);
    try {
      const res = await api.analyzeArticle(id, force);
      if (res.status === "quota_exceeded") {
        alert("AI 分析次数已用尽，请联系管理员增加配额");
        setAnalyzing(false);
        return;
      }
      if (res.status === "not_found") {
        alert("文章不存在");
        setAnalyzing(false);
        return;
      }
      if (res.status === "success" || res.status === "already_analyzed") {
        load();
        setAnalyzing(false);
        return;
      }
      let attempts = 0;
      pollRef.current = setInterval(async () => {
        attempts += 1;
        try {
          const updated = await api.getArticle(id);
          setArticle(updated);
          if (updated.analysis || attempts >= 15) {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setAnalyzing(false);
            if (!updated.analysis && attempts >= 15) {
              alert("分析耗时较长，请稍后刷新页面查看");
            }
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setAnalyzing(false);
        }
      }, 2000);
    } catch (e) {
      setAnalyzing(false);
      alert(e instanceof Error ? e.message : "AI 分析失败");
    }
  };

  if (loading) {
    return <p className="text-slate-500">加载中...</p>;
  }

  if (loadError || !article) {
    return (
      <div className="space-y-4">
        <Link href="/articles" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-primary-600">
          <ArrowLeft className="h-4 w-4" /> 返回知识库
        </Link>
        <p className="text-red-600">{loadError || "文章不存在"}</p>
      </div>
    );
  }

  const analysis = article.analysis;

  return (
    <div className="space-y-6">
      <Link href="/articles" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-primary-600">
        <ArrowLeft className="h-4 w-4" /> 返回知识库
      </Link>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <CardTitle className="text-xl leading-relaxed">{article.title}</CardTitle>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <span>{article.source_name}</span>
                <span>·</span>
                <span>{formatDate(article.publish_time || article.created_at)}</span>
                {article.publisher && <span>· {article.publisher}</span>}
                <Badge label={LEVEL_LABEL[article.policy_level] || article.policy_level} type={article.policy_level} />
                {analysis && <Badge label="AI 已梳理" type="policy" />}
                <a
                  href={article.article_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary-600 hover:underline"
                >
                  原文 <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              {analysis ? (
                <Button variant="secondary" size="sm" disabled={analyzing} onClick={() => handleAnalyze(true)}>
                  {analyzing ? (
                    <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-1 h-4 w-4" />
                  )}
                  重新分析
                </Button>
              ) : (
                <Button size="sm" disabled={analyzing} onClick={() => handleAnalyze(false)}>
                  {analyzing ? (
                    <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-1 h-4 w-4" />
                  )}
                  {analyzing ? "AI 分析中..." : "AI 提炼要点"}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <details className="group">
            <summary className="cursor-pointer text-sm font-medium text-slate-600 hover:text-primary-600">
              展开原文正文
            </summary>
            <div className="prose prose-sm mt-4 max-w-none whitespace-pre-wrap border-t pt-4 text-slate-700">
              {article.content || "暂无正文内容"}
            </div>
          </details>
          {article.attachments.length > 0 && (
            <div className="mt-4 border-t pt-4">
              <h4 className="mb-2 text-sm font-medium">附件</h4>
              <ul className="space-y-1">
                {article.attachments.map((a) => (
                  <li key={a.id}>
                    <a
                      href={a.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:underline"
                    >
                      {a.file_name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {!analysis && !analyzing && (
        <Card className="border-dashed border-amber-200 bg-gradient-to-r from-amber-50/80 to-orange-50/50">
          <CardContent className="flex items-center justify-between py-6">
            <div>
              <p className="font-medium text-slate-800">尚未进行 AI 梳理</p>
              <p className="mt-1 text-sm text-slate-500">自动提炼摘要、高亮关键词、标注截止时间与申报建议</p>
            </div>
            <Button onClick={() => handleAnalyze(false)}>
              <Sparkles className="mr-2 h-4 w-4" />
              开始 AI 分析
            </Button>
          </CardContent>
        </Card>
      )}

      {analyzing && !analysis && (
        <Card className="border-primary-100 bg-primary-50/30">
          <CardContent className="flex items-center gap-3 py-8 text-slate-600">
            <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
            <div>
              <p className="font-medium">正在调用 AI 分析政策要点</p>
              <p className="text-sm text-slate-500">预计 15–30 秒，请稍候...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {analysis && <AnalysisPanel analysis={analysis} />}
    </div>
  );
}
