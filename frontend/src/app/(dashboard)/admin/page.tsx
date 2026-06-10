"use client";

import { useEffect, useState } from "react";
import { api, AdminUser } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [multiUserEnabled, setMultiUserEnabled] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<number | null>(null);
  const [error, setError] = useState("");

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
    return <p className="text-slate-500">加载中…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">系统与用户管理</h1>
        <p className="mt-1 text-sm text-slate-500">系统开关、用户配额与账户状态</p>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">多用户模式</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              className="mt-1"
              checked={multiUserEnabled}
              disabled={settingsSaving}
              onChange={(e) => saveSettings(e.target.checked)}
            />
            <span className="text-sm text-slate-600">
              <span className="font-medium text-slate-800">开启多用户模式</span>
              <br />
              关闭后：首页与登录页隐藏公开注册；普通用户无法登录；已登录的普通用户将被拒绝访问 API。
              仅管理员账号可登录并使用系统。
            </span>
          </label>
          {!multiUserEnabled && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
              当前为单用户模式：公开注册与普通用户登录已关闭。
            </p>
          )}
        </CardContent>
      </Card>

      <div>
        <h2 className="text-lg font-semibold text-slate-900">用户与配额</h2>
        <p className="mt-1 text-sm text-slate-500">控制每位用户的采集次数与 AI 分析次数</p>
      </div>

      <div className="space-y-4">
        {users.map((u) => (
          <Card key={u.id}>
            <CardHeader className="pb-3">
              <CardTitle className="flex flex-wrap items-center gap-3 text-base">
                <span>{u.full_name || u.username}</span>
                <span className="text-sm font-normal text-slate-500">@{u.username}</span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{u.roles.join(", ")}</span>
                {!u.is_active && (
                  <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">已停用</span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label className="block text-sm">
                  <span className="text-slate-600">采集配额</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1"
                    value={u.crawl_quota}
                    onChange={(e) => patchLocal(u.id, "crawl_quota", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-600">已用采集</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1"
                    value={u.crawl_used}
                    onChange={(e) => patchLocal(u.id, "crawl_used", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-600">AI 配额</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1"
                    value={u.ai_quota}
                    onChange={(e) => patchLocal(u.id, "ai_quota", Number(e.target.value))}
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-600">已用 AI</span>
                  <Input
                    type="number"
                    min={0}
                    className="mt-1"
                    value={u.ai_used}
                    onChange={(e) => patchLocal(u.id, "ai_used", Number(e.target.value))}
                  />
                </label>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={u.is_active}
                    onChange={(e) => patchLocal(u.id, "is_active", e.target.checked)}
                  />
                  账户启用
                </label>
                <Button
                  size="sm"
                  disabled={saving === u.id}
                  onClick={() => updateUser(u.id, u)}
                >
                  {saving === u.id ? "保存中…" : "保存配额"}
                </Button>
                <span className="text-xs text-slate-400">
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
