"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { Globe, Play, Save, Target, X } from "lucide-react";
import {
  api,
  ColumnHealth,
  CrawlFilterMode,
  CrawlTaskCreate,
  MonitorTreeSource,
  ScheduleType,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { animateModalIn, animateModalOut } from "@/lib/gsap-motion";

const TYPE_LABEL: Record<string, string> = {
  moe: "国家级",
  provincial: "省级",
  university: "高校",
  research: "科研机构",
  other: "其他",
};

const COLUMN_LABEL: Record<string, string> = {
  notice: "通知公告",
  policy: "政策文件",
  project_apply: "项目申报",
};

const INTERVAL_PRESETS = [
  { label: "5分钟", minutes: 5 },
  { label: "15分钟", minutes: 15 },
  { label: "30分钟", minutes: 30 },
  { label: "60分钟", minutes: 60 },
];

const DAILY_TIME_PRESETS = ["07:00", "08:00", "09:00", "12:00", "18:00"];

interface Props {
  tree: MonitorTreeSource[];
  initialSourceId?: number | null;
  onClose: () => void;
  onSaved: () => void;
  onSyncPresets?: () => Promise<void>;
}

export function CrawlSetupPanel({ tree, initialSourceId, onClose, onSaved, onSyncPresets }: Props) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closingRef = useRef(false);
  const [loading, setLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState<Set<number>>(new Set());
  const [filterMode, setFilterMode] = useState<CrawlFilterMode>("column");
  const [selectedColumns, setSelectedColumns] = useState<Set<number>>(new Set());
  const [keywords, setKeywords] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [scheduleType, setScheduleType] = useState<ScheduleType>("interval");
  const [intervalMinutes, setIntervalMinutes] = useState(30);
  const [dailyTime, setDailyTime] = useState("08:00");
  const [autoCrawl, setAutoCrawl] = useState(true);
  const [columnHealth, setColumnHealth] = useState<Record<number, ColumnHealth>>({});
  const [healthLoading, setHealthLoading] = useState(false);

  useLayoutEffect(() => {
    const overlay = overlayRef.current;
    const panel = panelRef.current;
    if (!overlay || !panel) return;
    const ctx = gsap.context(() => animateModalIn(overlay, panel));
    return () => ctx.revert();
  }, []);

  const handleClose = () => {
    if (closingRef.current) return;
    const overlay = overlayRef.current;
    const panel = panelRef.current;
    if (!overlay || !panel) {
      onClose();
      return;
    }
    closingRef.current = true;
    animateModalOut(overlay, panel, () => {
      closingRef.current = false;
      onClose();
    });
  };

  useEffect(() => {
    if (initialSourceId) {
      setSelectedSources(new Set([initialSourceId]));
    }
  }, [initialSourceId]);

  useEffect(() => {
    const sourceId = [...selectedSources][0];
    if (!sourceId) {
      setColumnHealth({});
      return;
    }
    setHealthLoading(true);
    api
      .getColumnHealth(sourceId)
      .then((rows) => {
        const map = Object.fromEntries(rows.map((r) => [r.column_id, r]));
        setColumnHealth(map);
        const okIds = rows.filter((r) => r.status === "ok").map((r) => r.column_id);
        setSelectedColumns(new Set(okIds.length ? okIds : rows.map((r) => r.column_id)));
      })
      .catch(() => setColumnHealth({}))
      .finally(() => setHealthLoading(false));
  }, [selectedSources]);

  const activeSources = useMemo(
    () => tree.filter((s) => selectedSources.has(s.id)),
    [tree, selectedSources]
  );

  const availableColumns = useMemo(
    () => activeSources.flatMap((s) => s.columns.map((c) => ({ ...c, sourceName: s.name }))),
    [activeSources]
  );

  const resolveTargetColumnIds = (): number[] => {
    if (selectedSources.size === 0) return [];
    if (selectedColumns.size > 0) return [...selectedColumns];
    return availableColumns.map((c) => c.id);
  };

  const toggleSource = (id: number) => {
    setSelectedSources(new Set([id]));
  };

  const healthBadge = (health?: ColumnHealth) => {
    if (!health) return { label: healthLoading ? "检测中" : "未检测", type: "inactive" as const };
    if (health.status === "ok") return { label: `正常 · ${health.list_count}条`, type: "active" as const };
    if (health.status === "empty") return { label: "待配置", type: "notice" as const };
    return { label: "链接失效", type: "inactive" as const };
  };

  const buildPlanPayload = (): CrawlTaskCreate | null => {
    const ids = resolveTargetColumnIds();
    if (ids.length === 0 || selectedSources.size !== 1) return null;
    const sourceId = [...selectedSources][0];
    const payload: CrawlTaskCreate = {
      source_id: sourceId,
      column_ids: ids,
      schedule_type: scheduleType,
      auto_crawl_enabled: scheduleType === "manual" ? false : autoCrawl,
      crawl_filter_mode: filterMode,
    };
    if (scheduleType === "interval") {
      if (intervalMinutes < 5) return null;
      payload.crawl_interval = intervalMinutes;
    }
    if (scheduleType === "daily") payload.daily_crawl_time = dailyTime;
    if (filterMode === "keyword") {
      const kws = keywords.split(/[,，\s]+/).map((k) => k.trim()).filter(Boolean);
      if (kws.length === 0) return null;
      payload.filter_keywords = kws;
    }
    if (filterMode === "date_range") {
      if (!dateFrom && !dateTo) return null;
      if (dateFrom) payload.filter_date_from = dateFrom;
      if (dateTo) payload.filter_date_to = dateTo;
    }
    return payload;
  };

  const handleSave = async () => {
    const payload = buildPlanPayload();
    if (!payload) return alert("请选择一个采集源并完善采集配置");
    const broken = payload.column_ids.filter((id) => columnHealth[id]?.status === "error");
    if (broken.length) return alert("所选板块含失效链接，请取消勾选或先同步预设网站后重试");
    setLoading(true);
    try {
      await api.createCrawlTask(payload);
      alert("采集任务已创建");
      onSaved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    const payload = buildPlanPayload();
    if (!payload) return alert("请选择一个采集源并完善采集配置");
    const broken = payload.column_ids.filter((id) => columnHealth[id]?.status === "error");
    if (broken.length) return alert("所选板块含失效链接，请取消勾选或先同步预设网站后重试");
    setLoading(true);
    try {
      const task = await api.createCrawlTask(payload);
      const r = await api.startCrawlTask(task.id);
      if (r.results?.length) {
        const added = r.results.reduce((sum, item) => sum + (item.new || 0), 0);
        alert(`采集完成：新增 ${added} 条`);
      } else {
        alert(`已开始采集 ${r.count} 个栏目`);
      }
      onSaved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "采集启动失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 pt-12"
    >
      <div ref={panelRef} className="w-full max-w-3xl rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">新建采集任务</h3>
            <p className="text-sm text-slate-500">选择采集源 → 配置计划 → 保存（不影响预设网站）</p>
          </div>
          <button type="button" onClick={handleClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[70vh] space-y-6 overflow-y-auto px-6 py-5">
          {/* 选择网站 */}
          <section>
            <h4 className="mb-3 text-sm font-semibold text-slate-800">1. 选择采集源</h4>
            {tree.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
                <Globe className="mx-auto mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm font-medium text-slate-700">暂无预设网站，无法创建采集任务</p>
                <p className="mt-1 text-xs text-slate-500">
                  预设网站是固定的教育官网目录；采集任务是单独创建的定时计划。
                </p>
                {onSyncPresets && (
                  <Button className="mt-4" size="sm" onClick={() => onSyncPresets()}>
                    同步预设源（教育部 + 各省官网）
                  </Button>
                )}
              </div>
            ) : (
              <div className="grid max-h-40 grid-cols-2 gap-2 overflow-y-auto">
                {tree.map((s) => (
                  <label
                    key={s.id}
                    className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                      selectedSources.has(s.id) ? "border-primary-400 bg-primary-50" : "border-slate-200"
                    }`}
                  >
                  <input
                    type="radio"
                    name="crawl-source"
                    checked={selectedSources.has(s.id)}
                    onChange={() => toggleSource(s.id)}
                  />
                    <Globe className="h-3.5 w-3.5 text-primary-600" />
                    <span className="line-clamp-1">{s.name}</span>
                    <Badge label={TYPE_LABEL[s.type] || s.type} />
                    {s.status === "inactive" && <Badge label="已停用" type="inactive" />}
                  </label>
                ))}
              </div>
            )}
          </section>

          {/* 采集模式 */}
          <section>
            <h4 className="mb-3 text-sm font-semibold text-slate-800">2. 采集模式</h4>
            <div className="mb-3 flex flex-wrap gap-2">
              {(["column", "keyword", "date_range"] as CrawlFilterMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setFilterMode(m)}
                  className={`rounded-lg px-3 py-1.5 text-sm ${
                    filterMode === m ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {m === "column" ? "指定栏目" : m === "keyword" ? "关键词" : "时间范围"}
                </button>
              ))}
            </div>
            <div className="mb-2 rounded-lg border border-amber-100 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
              各省政府官网栏目路径不同，请勾选该网站<strong>实际可访问的板块</strong>。
              若采集为 0，请先点「同步预设网站」更新栏目地址，或改用「指定栏目」全量采集测试。
            </div>
            <div className="max-h-44 space-y-1 overflow-y-auto rounded-lg bg-slate-50 p-3">
              <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-500">
                <span>采集板块（可多选）</span>
                {healthLoading && <span className="text-primary-600">正在检测栏目链接…</span>}
              </div>
              {availableColumns.map((c) => {
                const hb = healthBadge(columnHealth[c.id]);
                return (
                  <label
                    key={c.id}
                    className="flex cursor-pointer items-center gap-2 rounded-lg px-1 py-1.5 text-sm hover:bg-white"
                    title={columnHealth[c.id]?.message}
                  >
                    <input
                      type="checkbox"
                      checked={selectedColumns.has(c.id)}
                      disabled={columnHealth[c.id]?.status === "error"}
                      onChange={() =>
                        setSelectedColumns((prev) => {
                          const n = new Set(prev);
                          if (n.has(c.id)) n.delete(c.id);
                          else n.add(c.id);
                          return n;
                        })
                      }
                    />
                    <span className="min-w-0 flex-1">
                      <span className="text-slate-500">{c.sourceName}</span>
                      <span className="mx-1 text-slate-300">·</span>
                      <span>{c.column_name}</span>
                    </span>
                    <Badge label={hb.label} type={hb.type} />
                  </label>
                );
              })}
            </div>
            {filterMode === "keyword" && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-slate-500">
                  在已选板块内遍历列表，进入文章详情后按<strong>标题或正文</strong>匹配；多个关键词为「或」关系，命中任一即采集。
                </p>
                <Input
                  placeholder="例如：招生, 义务教育, 项目申报（逗号或空格分隔）"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                />
              </div>
            )}
            {filterMode === "date_range" && (
              <div className="space-y-2">
                <p className="text-xs text-slate-500">
                  在已选板块内采集，并按文章发布时间过滤；列表无日期时会进入详情页再判断。
                </p>
                <div className="flex gap-3">
                  <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                </div>
              </div>
            )}
          </section>

          {/* 检测频率 */}
          <section>
            <h4 className="mb-3 text-sm font-semibold text-slate-800">3. 检测频率</h4>
            <div className="mb-3 flex flex-wrap gap-2">
              {(["interval", "daily", "manual"] as ScheduleType[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setScheduleType(s)}
                  className={`rounded-lg px-3 py-1.5 text-sm ${
                    scheduleType === s ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {s === "interval" ? "按间隔" : s === "daily" ? "每天定时" : "仅手动"}
                </button>
              ))}
            </div>
            {scheduleType === "interval" && (
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {INTERVAL_PRESETS.map((p) => (
                    <button
                      key={p.minutes}
                      type="button"
                      onClick={() => setIntervalMinutes(p.minutes)}
                      className={`rounded-full px-3 py-1 text-xs ${
                        intervalMinutes === p.minutes
                          ? "bg-primary-600 text-white"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={autoCrawl} onChange={(e) => setAutoCrawl(e.target.checked)} />
                  开启自动巡检
                </label>
              </div>
            )}
            {scheduleType === "daily" && (
              <div className="flex flex-wrap items-center gap-2">
                <Input type="time" className="w-32" value={dailyTime} onChange={(e) => setDailyTime(e.target.value)} />
                {DAILY_TIME_PRESETS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setDailyTime(t)}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-xs"
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
          </section>

          <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
            <div className="flex items-center gap-1 font-medium text-slate-800">
              <Target className="h-3.5 w-3.5" />
              目标栏目 {resolveTargetColumnIds().length} 个
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t px-6 py-4">
          <Button variant="secondary" onClick={handleClose}>
            取消
          </Button>
          <Button variant="secondary" disabled={loading || tree.length === 0} onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            保存计划
          </Button>
          <Button disabled={loading || tree.length === 0} onClick={handleStart}>
            <Play className="mr-2 h-4 w-4" />
            保存并开始采集
          </Button>
        </div>
      </div>
    </div>
  );
}
