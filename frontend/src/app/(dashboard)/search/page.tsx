"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { api, ArticleListItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const SUGGESTIONS = ["职业教育", "双高建设", "人工智能", "产教融合", "教育数字化", "实训基地"];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ArticleListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const doSearch = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await api.searchArticles(q);
      setResults(res.items);
      setTotal(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="py-6">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                className="pl-10"
                placeholder="搜索政策关键词，如：职业教育、双高建设..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && doSearch(query)}
              />
            </div>
            <Button onClick={() => doSearch(query)} disabled={loading}>
              {loading ? "搜索中..." : "搜索"}
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => { setQuery(s); doSearch(s); }}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 hover:bg-primary-50 hover:text-primary-700"
              >
                {s}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {total > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>找到 {total} 条结果</CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-slate-100 p-0">
            {results.map((a) => (
              <Link
                key={a.id}
                href={`/articles/${a.id}`}
                className="block px-6 py-4 hover:bg-slate-50"
              >
                <p className="font-medium text-slate-900">{a.title}</p>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                  <span>{a.source_name}</span>
                  <span>·</span>
                  <span>{formatDate(a.publish_time || a.created_at)}</span>
                  {a.has_analysis && <Badge label="已解读" type="policy" />}
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
