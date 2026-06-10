"use client";

import { useState } from "react";
import Link from "next/link";
import { Bot, Send } from "lucide-react";
import { api, QAResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const EXAMPLES = [
  "最近有哪些职业教育项目？",
  "双高建设相关政策有哪些？",
  "产教融合方面有什么新通知？",
];

export default function QAPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QAResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const ask = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await api.askQA(q);
      setResult(res);
    } catch {
      alert("问答失败，请检查 DeepSeek API 配置");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary-600" />
            AI 政策问答
          </CardTitle>
          <p className="text-sm text-slate-500">基于知识库检索 + DeepSeek 生成回答</p>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="请输入您的问题..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask(question)}
            />
            <Button onClick={() => ask(question)} disabled={loading}>
              <Send className="mr-1 h-4 w-4" />
              {loading ? "思考中..." : "提问"}
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => { setQuestion(ex); ask(ex); }}
                className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs text-slate-600 hover:bg-primary-50 hover:text-primary-700"
              >
                {ex}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">回答</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{result.answer}</p>
            </CardContent>
          </Card>

          {result.related_articles.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">相关政策</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.related_articles.map((a) => (
                  <Link
                    key={a.id}
                    href={`/articles/${a.id}`}
                    className="block rounded-lg border border-slate-100 p-3 text-sm hover:border-primary-200 hover:bg-primary-50/30"
                  >
                    <p className="font-medium text-slate-900">{a.title}</p>
                    <p className="text-xs text-slate-500">{a.source}</p>
                  </Link>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
