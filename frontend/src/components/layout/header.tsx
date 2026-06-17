"use client";

import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { api, clearToken, User } from "@/lib/api";
import { capsuleHeaderClass } from "@/lib/landing-theme";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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
    <div className="sticky top-0 z-30 px-8 pt-5">
      <header
        className={cn(
          capsuleHeaderClass,
          "flex h-[3.25rem] items-center justify-between px-6"
        )}
      >
        <div>
          <h2 className="text-base font-semibold tracking-tight text-slate-900">{title}</h2>
          {user && (
            <p className="text-[11px] text-slate-400">
              {user.full_name || user.username}
              {user.roles[0] !== "admin" && (
                <span className="ml-2">
                  · 采集 {user.crawl_used}/{user.crawl_quota} · AI {user.ai_used}/{user.ai_quota}
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="hidden rounded-full bg-slate-100/90 px-3 py-1 text-xs font-medium text-slate-600 sm:inline">
              {user.roles[0]}
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="rounded-full text-slate-600 hover:bg-blue-50 hover:text-blue-600"
          >
            <LogOut className="mr-1.5 h-4 w-4" />
            退出
          </Button>
        </div>
      </header>
    </div>
  );
}
