"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import Link from "next/link";
import {
  Activity,
  ExternalLink,
  Globe,
  Layers,
  ListTodo,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Zap,
} from "lucide-react";
import {
  api,
  ArticleListItem,
  CrawlLog,
  CrawlTask,
  MonitorStats,
  MonitorTreeSource,
} from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { CrawlSetupPanel } from "@/components/monitor/crawl-setup-panel";
import { fadeUp, revealIn, staggerReveal } from "@/lib/gsap-motion";

const TYPE_LABEL: Record<string, string> = {
  moe: "国家级",
  provincial: "省级",
  university: "高校",
  research: "科研机构",
  government: "政府公开",
  other: "其他",
};

const TYPE_BADGE: Record<string, "policy" | "notice" | "active" | "inactive"> = {
  moe: "policy",
  provincial: "notice",
  university: "active",
  research: "inactive",
  other: "inactive",
};

type TabKey = "sources" | "tasks" | "content";

export default function MonitorPage() {
  const [tab, setTab] = useState<TabKey>("tasks");
  const [stats, setStats] = useState<MonitorStats | null>(null);
  const [tree, setTree] = useState<MonitorTreeSource[]>([]);
  const [tasks, setTasks] = useState<CrawlTask[]>([]);
  const [logs, setLogs] = useState<CrawlLog[]>([]);
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [showSetup, setShowSetup] = useState(false);
  const [setupSourceId, setSetupSourceId] = useState<number | null>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const statsGridRef = useRef<HTMLDivElement>(null);
  const tabPanelRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => fadeUp(headerRef.current));
    return () => ctx.revert();
  }, []);

  useLayoutEffect(() => {
    if (!stats) return;
    const ctx = gsap.context(() => {
      staggerReveal(statsGridRef.current, "[data-stagger]", { stagger: 0.08 });
    }, statsGridRef);
    return () => ctx.revert();
  }, [stats]);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => revealIn(tabPanelRef.current));
    return () => ctx.revert();
  }, [tab]);

  const load = async () => {
    setLoading(true);
    try {
      const [boot, crawlLogs, recent] = await Promise.all([
        api.bootstrapMonitor(),
        api.getCrawlLogs().catch(() => []),
        api.getArticles({ limit: 15 }).then((r) => r.items).catch(() => []),
      ]);
      setTree(boot.tree ?? []);
      setTasks(boot.tasks ?? []);
      setStats(boot.stats ?? null);
      setLogs(crawlLogs);
      setArticles(recent);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const filteredSources = useMemo(() => {
    return tree.filter((s) => {
      const matchSearch =
        !search ||
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.url.toLowerCase().includes(search.toLowerCase());
      const matchType = typeFilter === "all" || s.type === typeFilter;
      return matchSearch && matchType;
    });
  }, [tree, search, typeFilter]);

  const pausedTasks = useMemo(() => tasks.filter((t) => !t.is_active), [tasks]);

  const statCards = stats
    ? [
        { label: "预设网站", value: stats.total_sources, icon: Globe, color: "text-blue-600 bg-blue-50" },
        { label: "可采栏目", value: stats.total_columns, icon: Layers, color: "text-violet-600 bg-violet-50" },
        { label: "采集任务", value: stats.total_tasks ?? tasks.length, icon: ListTodo, color: "text-indigo-600 bg-indigo-50" },
        { label: "运行中", value: stats.running_tasks, icon: Activity, color: "text-emerald-600 bg-emerald-50" },
        { label: "今日采集", value: stats.today_collected, icon: Zap, color: "text-orange-600 bg-orange-50" },
      ]
    : [];

  const handleSyncPresets = async (keepSetupOpen = false) => {
    if (!keepSetupOpen && !confirm("将补全缺失的预设网站（不会创建采集任务），是否继续？")) return;
    setLoading(true);
    try {
      const r = await api.syncPresetSources();
      if (!keepSetupOpen) {
        alert(
          `已同步：新增 ${r.created_sources} 个网站、${r.created_columns} 个栏目；更新 ${r.updated_columns ?? 0} 个栏目地址`
        );
      }
      await load();
    } catch {
      alert("同步失败");
    } finally {
      setLoading(false);
    }
  };

  const handlePauseAllTasks = async () => {
    if (!confirm(`暂停全部 ${tasks.length} 个采集任务？预设网站不受影响。`)) return;
    setLoading(true);
    try {
      const r = await api.pauseAllTasks();
      alert(`已暂停 ${r.paused_tasks} 个采集任务`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "操作失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePausedTasks = async () => {
    if (pausedTasks.length === 0) return alert("没有已暂停的采集任务");
    if (!confirm(`删除 ${pausedTasks.length} 个已暂停的采集任务？预设网站将保留。`)) return;
    setLoading(true);
    try {
      const r = await api.deletePausedTasks();
      alert(`已删除 ${r.deleted} 个采集任务`);
      load();
    } catch {
      alert("删除失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTask = async (task: CrawlTask) => {
    if (task.is_active) return alert("请先暂停该任务后再删除");
    if (!confirm(`确定删除采集任务「${task.name}」？`)) return;
    try {
      await api.deleteCrawlTask(task.id);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "删除失败");
    }
  };

  const handleToggleTask = async (task: CrawlTask) => {
    try {
      const updated = await api.toggleCrawlTask(task.id);
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      if (stats) {
        const wasRunning = task.is_active && task.running;
        const nowRunning = updated.is_active && updated.running;
        if (wasRunning !== nowRunning) {
          setStats({
            ...stats,
            running_tasks: Math.max(0, stats.running_tasks + (nowRunning ? 1 : -1)),
          });
        }
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "操作失败");
    }
  };

  const handleStartTask = async (task: CrawlTask) => {
    setLoading(true);
    try {
      const r = await api.startCrawlTask(task.id);
      if (r.results?.length) {
        const added = r.results.reduce((sum, item) => sum + (item.new || 0), 0);
        const skipped = r.results.reduce((sum, item) => sum + (item.skipped_by_filter || 0), 0);
        const hints = r.results
          .map((item) => item.hint)
          .filter(Boolean)
          .slice(0, 2)
          .join("\n");
        const extra = skipped > 0 ? `\n（${skipped} 条未通过任务筛选条件）` : "";
        alert(
          hints ? `采集完成：新增 ${added} 条${extra}\n\n${hints}` : `采集完成：新增 ${added} 条${extra}`
        );
      } else {
        alert(`已开始采集 ${r.count} 个栏目`);
      }
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "采集失败");
    } finally {
      setLoading(false);
    }
  };

  const openSetup = (sourceId?: number) => {
    setSetupSourceId(sourceId ?? null);
    setShowSetup(true);
  };

  return (
    <div className="space-y-6">
      <div ref={headerRef} className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">数据采集中心</h2>
          <p className="mt-1 text-sm text-slate-500">
            预设网站固定存在；采集任务单独创建，删除任务不会影响网站
          </p>
        </div>
        <Button onClick={() => openSetup()}>
          <Plus className="mr-2 h-4 w-4" />
          新建采集任务
        </Button>
      </div>

      <div ref={statsGridRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.label} data-stagger>
              <CardContent className="flex items-center gap-4 py-5">
                <div className={`rounded-xl p-3 ${c.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">{c.label}</p>
                  <p className="text-2xl font-bold text-slate-900">{c.value}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {!stats && (
          <div className="col-span-full py-4 text-center text-sm text-slate-400">加载统计中...</div>
        )}
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-1">
          {([
            { key: "tasks" as TabKey, label: "采集任务" },
            { key: "sources" as TabKey, label: "预设网站" },
            { key: "content" as TabKey, label: "采集内容" },
          ]).map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`border-b-2 px-4 py-3 text-sm font-medium transition ${
                tab === t.key
                  ? "border-primary-600 text-primary-700"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div ref={tabPanelRef}>
      {tab === "tasks" && (
        <div className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-4 py-3">
                <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
                  <RefreshCw className={`mr-1 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  刷新
                </Button>
                <Button variant="secondary" size="sm" disabled={loading || tasks.length === 0} onClick={handlePauseAllTasks}>
                  <Pause className="mr-1 h-4 w-4" />
                  全部暂停
                </Button>
                {pausedTasks.length > 0 && (
                  <Button variant="danger" size="sm" disabled={loading} onClick={handleDeletePausedTasks}>
                    <Trash2 className="mr-1 h-4 w-4" />
                    删除已暂停 ({pausedTasks.length})
                  </Button>
                )}
                <Button size="sm" onClick={() => openSetup()}>
                  <Plus className="mr-1 h-4 w-4" />
                  新建任务
                </Button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-slate-50 text-left text-xs font-medium text-slate-500">
                    <tr>
                      <th className="px-4 py-3">任务名称</th>
                      <th className="px-4 py-3">采集源</th>
                      <th className="px-4 py-3">栏目</th>
                      <th className="px-4 py-3">计划</th>
                      <th className="px-4 py-3">筛选</th>
                      <th className="px-4 py-3">最近同步</th>
                      <th className="px-4 py-3">状态</th>
                      <th className="px-4 py-3 text-right">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {tasks.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50/80">
                        <td className="px-4 py-3 font-medium text-slate-900">{t.name}</td>
                        <td className="px-4 py-3 text-slate-700">{t.source_name}</td>
                        <td className="px-4 py-3 text-slate-600">{t.column_names.join("、") || "—"}</td>
                        <td className="px-4 py-3 text-slate-600">{t.schedule_label}</td>
                        <td className="px-4 py-3 text-slate-500">{t.filter_label}</td>
                        <td className="px-4 py-3 text-slate-500">
                          {t.last_crawled_at ? formatDate(t.last_crawled_at) : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            label={t.is_active && t.running ? "运行中" : t.is_active ? "已启用" : "已暂停"}
                            type={t.is_active && t.running ? "active" : "inactive"}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => handleToggleTask(t)}
                              className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                              title={t.is_active ? "暂停" : "启用"}
                            >
                              {t.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleStartTask(t)}
                              className="rounded-lg p-2 text-slate-400 hover:bg-primary-50 hover:text-primary-600"
                              title="立即采集"
                            >
                              <RefreshCw className="h-4 w-4" />
                            </button>
                            {!t.is_active && (
                              <button
                                type="button"
                                onClick={() => handleDeleteTask(t)}
                                className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                                title="删除任务"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {tasks.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                          暂无采集任务，点击「新建采集任务」选择采集源并配置
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <div className="border-b px-4 py-3 text-sm font-medium text-slate-800">采集日志</div>
              <table className="w-full text-sm">
                <thead className="border-b bg-slate-50 text-left text-xs text-slate-500">
                  <tr>
                    <th className="px-4 py-2">来源</th>
                    <th className="px-4 py-2">栏目</th>
                    <th className="px-4 py-2">状态</th>
                    <th className="px-4 py-2">新增</th>
                    <th className="px-4 py-2">时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {logs.slice(0, 15).map((l) => (
                    <tr key={l.id}>
                      <td className="px-4 py-2 text-slate-600">{l.source_name || "—"}</td>
                      <td className="px-4 py-2">{l.column_name || `#${l.column_id}`}</td>
                      <td className="px-4 py-2">
                        <Badge label={l.status} type={l.status === "success" ? "active" : "inactive"} />
                      </td>
                      <td className="px-4 py-2 text-green-600">+{l.new_count}</td>
                      <td className="px-4 py-2 text-slate-500">{formatDate(l.created_at)}</td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                        暂无采集记录
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "sources" && (
        <Card>
          <CardContent className="p-0">
            <div className="border-b border-blue-100 bg-blue-50/60 px-4 py-2.5 text-xs text-blue-800">
              <strong>预设网站</strong>为固定目录（教育部 + 各省官网），仅展示可采集的栏目，不支持删除。
              需要采集时请切换到「采集任务」新建任务。
            </div>
            <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-4 py-3">
              <div className="relative min-w-[220px] flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  className="pl-9"
                  placeholder="搜索网站..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <select
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">全部类型</option>
                <option value="moe">国家级</option>
                <option value="provincial">省级</option>
              </select>
              <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
                <RefreshCw className={`mr-1 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </Button>
              <Button variant="secondary" size="sm" disabled={loading} onClick={() => handleSyncPresets()}>
                同步预设网站
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-slate-50 text-left text-xs font-medium text-slate-500">
                  <tr>
                    <th className="px-4 py-3">网站名称</th>
                    <th className="px-4 py-3">类型</th>
                    <th className="px-4 py-3">栏目数</th>
                    <th className="px-4 py-3">采集任务</th>
                    <th className="px-4 py-3">已采文章</th>
                    <th className="px-4 py-3 text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredSources.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/80">
                      <td className="px-4 py-3">
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 rounded-lg bg-slate-100 p-2">
                            <Globe className="h-4 w-4 text-slate-500" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-slate-900">{s.name}</p>
                            <p className="mt-0.5 truncate text-xs text-slate-400">{s.url}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge label={TYPE_LABEL[s.type] || s.type} type={TYPE_BADGE[s.type] || "inactive"} />
                      </td>
                      <td className="px-4 py-3 text-slate-700">{s.column_count ?? s.columns.length}</td>
                      <td className="px-4 py-3 text-slate-700">{s.task_count ?? 0} 个</td>
                      <td className="px-4 py-3 font-medium text-slate-800">
                        {(s.article_count ?? 0).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                            title="打开网站"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                          <Button variant="ghost" size="sm" onClick={() => openSetup(s.id)}>
                            新建任务
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {filteredSources.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-slate-400">
                        {tree.length === 0
                          ? "暂无预设网站，系统将自动同步；也可点击「同步预设网站」"
                          : "没有匹配的网站"}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {tab === "content" && (
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <span className="text-sm font-medium text-slate-800">最近采集内容</span>
              <Link href="/articles" className="text-sm text-primary-600 hover:underline">
                查看全部政策 →
              </Link>
            </div>
            <div className="divide-y">
              {articles.map((a) => (
                <Link
                  key={a.id}
                  href={`/articles/${a.id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 transition hover:bg-slate-50"
                >
                  <div className="min-w-0 flex-1">
                    <p className="line-clamp-1 text-sm font-medium text-slate-900">{a.title}</p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {a.source_name || "未知来源"} · {formatDate(a.publish_time || a.created_at)}
                    </p>
                  </div>
                  {a.has_analysis && <Badge label="已解读" type="policy" />}
                </Link>
              ))}
              {articles.length === 0 && (
                <p className="px-4 py-12 text-center text-sm text-slate-400">暂无采集内容</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      </div>

      {showSetup && (
        <CrawlSetupPanel
          tree={tree}
          initialSourceId={setupSourceId}
          onClose={() => {
            setShowSetup(false);
            setSetupSourceId(null);
          }}
          onSaved={() => {
            setShowSetup(false);
            setSetupSourceId(null);
            load();
          }}
          onSyncPresets={() => handleSyncPresets(true)}
        />
      )}
    </div>
  );
}
