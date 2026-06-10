"use client";

import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { api, clearToken, User } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function Header({ title }: { title: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  const logout = () => {
    clearToken();
    window.location.href = "/login";
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-8 backdrop-blur">
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span>
              {user.full_name || user.username}
              <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs">
                {user.roles[0]}
              </span>
            </span>
            {user.roles[0] !== "admin" && (
              <span className="hidden text-xs text-slate-500 sm:inline">
                采集 {user.crawl_used}/{user.crawl_quota} · AI {user.ai_used}/{user.ai_quota}
              </span>
            )}
          </div>
        )}
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="mr-1 h-4 w-4" />
          退出
        </Button>
      </div>
    </header>
  );
}
