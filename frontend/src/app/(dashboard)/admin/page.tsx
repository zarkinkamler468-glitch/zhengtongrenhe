"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Database,
  Settings2,
  Shield,
  Sparkles,
  ToggleLeft,
  Users,
} from "lucide-react";
import { api, AdminUser } from "@/lib/api";
import { glassPanelClass, pageEyebrowClass } from "@/lib/landing-theme";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function StatTile({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: string | number;
  tone: string;
}) {
  return (
    <div className={cn(glassPanelClass, "flex items-center gap-4 p-5")}>
      <div className={cn("flex h-11 w-11 items-center justify-center rounded-2xl text-white shadow-lg", tone)}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [multiUserEnabled, setMultiUserEnabled] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<number | null>(null);
  const [error, setError] = useState("");

  const stats = useMemo(() => {
    const active = users.filter((u) => u.is_active).length;
    const totalCrawl = users.reduce((s, u) => s + u.crawl_quota, 0);
    const totalAi = users.reduce((s, u) => s + u.ai_quota, 0);
    return { active, totalCrawl, totalAi };
  }, [users]);

  const load = () => {
    setLoading(true);
    Promise.all([api.listAdminUsers(), api.getAdminSettings()])
      .then(([userList, settings]) => {
        setUsers(userList);
        setMultiUserEnabled(settings.multi_user_enabled);
        setError("");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    api.me().then((u) => {
      if (!u.roles.includes("admin")) {
        setError("仅管理员可访问此页面");
        setLoading(false);
        return;
      }
      load();
    }).catch(() => {
      setError("无法验证权限");
      setLoading(false);
    });
  }, []);

  const saveSettings = async (enabled: boolean) => {
    setSettingsSaving(true);
    setError("");
    try {
      const settings = await api.updateAdminSettings({ multi_user_enabled: enabled });
      setMultiUserEnabled(settings.multi_user_enabled);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存系统设置失败");
    } finally {
      setSettingsSaving(false);
    }
  };

  const updateUser = async (id: number, patch: Partial<AdminUser>) => {
    setSaving(id);
    try {
      const updated = await api.updateAdminUser(id, {
        crawl_quota: patch.crawl_quota,
        ai_quota: patch.ai_quota,
        crawl_used: patch.crawl_used,
        ai_used: patch.ai_used,
        is_active: patch.is_active,
      });
      setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(null);
    }
  };

  const patchLocal = (id: number, field: keyof AdminUser, value: number | boolean) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, [field]: value } : u))
    );
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <p className="text-sm text-slate-500">加载中…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <p className={pageEyebrowClass}>Administration</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">系统与用户管理</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          系统开关、用户配额与账户状态。界面风格与首页一致，便于统一运营体验。
        </p>
      </div>

      {error && (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 backdrop-blur-sm">
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile icon={Users} label="注册用户" value={users.length} tone="bg-blue-500" />
        <StatTile icon={Shield} label="活跃账户" value={stats.active} tone="bg-emerald-500" />
        <StatTile icon={Database} label="采集配额合计" value={stats.totalCrawl} tone="bg-violet-500" />
        <StatTile icon={Sparkles} label="AI 配额合计" value={stats.totalAi} tone="bg-indigo-500" />
      </div>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center gap-3 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-500/25">
            <Settings2 className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base">多用户模式</CardTitle>
            <p className="text-xs text-slate-500">控制公开注册与普通用户登录</p>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex cursor-pointer items-start gap-4 rounded-2xl border border-white/80 bg-white/50 p-4 transition hover:bg-white/70">
            <button
              type="button"
              role="switch"
              aria-checked={multiUserEnabled}
              disabled={settingsSaving}
              onClick={() => saveSettings(!multiUserEnabled)}
              className={cn(
                "relative mt-0.5 h-7 w-12 shrink-0 rounded-full transition-colors",
                multiUserEnabled ? "bg-blue-600" : "bg-slate-300",
                settingsSaving && "opacity-60"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform",
                  multiUserEnabled ? "left-[1.375rem]" : "left-0.5"
                )}
              />
            </button>
            <span className="text-sm text-slate-600">
              <span className="font-semibold text-slate-800">开启多用户模式</span>
              <br />
              关闭后：首页与登录页隐藏公开注册；普通用户无法登录；已登录的普通用户将被拒绝访问 API。
              仅管理员账号可登录并使用系统。
            </span>
          </label>
          {!multiUserEnabled && (
            <p className="flex items-center gap-2 rounded-2xl border border-amber-200/80 bg-amber-50/90 px-4 py-3 text-sm text-amber-800">
              <ToggleLeft className="h-4 w-4 shrink-0" />
              当前为单用户模式：公开注册与普通用户登录已关闭。
            </p>
          )}
        </CardContent>
      </Card>

      <div>
        <p className={pageEyebrowClass}>Users</p>
        <h2 className="mt-2 text-xl font-bold text-slate-900">用户与配额</h2>
        <p className="mt-1 text-sm text-slate-500">控制每位用户的采集次数与 AI 分析次数</p>
      </div>

      <div className="space-y-4">
        {users.map((u) => (
          <Card key={u.id} className="overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                <span className="font-semibold">{u.full_name || u.username}</span>
                <span className="text-sm font-normal text-slate-400">@{u.username}</span>
                <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-blue-100">
                  {u.roles.join(", ")}
                </span>
                {!u.is_active && (
                  <span className="rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 ring-1 ring-red-100">
                    已停用
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label className="block text-sm">
                  <span className="font-medium text-slate-600">采集配额</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1.5"
                    value={u.crawl_quota}
                    onChange={(e) => patchLocal(u.id, "crawl_quota", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-slate-600">已用采集</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1.5"
                    value={u.crawl_used}
                    onChange={(e) => patchLocal(u.id, "crawl_used", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-slate-600">AI 配额</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1.5"
                    value={u.ai_quota}
                    onChange={(e) => patchLocal(u.id, "ai_quota", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-slate-600">已用 AI</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1.5"
                    value={u.ai_used}
                    onChange={(e) => patchLocal(u.id, "ai_used", Number(e.target.value))}
                  />
                </label>
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-white/60 pt-4">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    checked={u.is_active}
                    onChange={(e) => patchLocal(u.id, "is_active", e.target.checked)}
                  />
                  账户启用
                </label>
                <Button
                  size="sm"
                  disabled={saving === u.id}
                  onClick={() => updateUser(u.id, u)}
                  className="rounded-full px-5"
                >
                  {saving === u.id ? "保存中…" : "保存配额"}
                </Button>
                <span className="rounded-full bg-slate-100/80 px-3 py-1 text-xs text-slate-500">
                  剩余采集 {Math.max(0, u.crawl_quota - u.crawl_used)} · 剩余 AI{" "}
                  {Math.max(0, u.ai_quota - u.ai_used)}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
