"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bell,
  BookOpen,
  Database,
  LayoutDashboard,
  MessageSquare,
  Radar,
  Search,
  Sparkles,
  Users,
} from "lucide-react";
import { api, User } from "@/lib/api";
import { glassPanelClass, sidebarShellClass } from "@/lib/landing-theme";
import { cn } from "@/lib/utils";
import { prefersReducedMotion } from "@/lib/gsap-motion";

type NavItem = { href: string; label: string; icon?: LucideIcon };
type NavGroup = { title: string; items: NavItem[] };

const baseGroups: NavGroup[] = [
  {
    title: "概览",
    items: [{ href: "/dashboard", label: "数据概览", icon: LayoutDashboard }],
  },
  {
    title: "核心功能",
    items: [
      { href: "/monitor", label: "数据采集中心", icon: Database },
      { href: "/articles", label: "政策知识库", icon: BookOpen },
      { href: "/search", label: "全文检索", icon: Search },
      { href: "/qa", label: "AI 政策问答", icon: MessageSquare },
    ],
  },
  {
    title: "运营管理",
    items: [
      { href: "/subscriptions", label: "关键词订阅", icon: Bell },
      { href: "/analytics", label: "数据分析", icon: BarChart3 },
    ],
  },
];

function isActive(pathname: string, href: string) {
  return pathname === href || (href !== "/" && pathname.startsWith(href));
}

export function Sidebar() {
  const pathname = usePathname();
  const navRef = useRef<HTMLElement>(null);
  const indicatorRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  const groups = useMemo(() => {
    const g = [...baseGroups];
    if (user?.roles.includes("admin")) {
      g.push({
        title: "系统管理",
        items: [{ href: "/admin", label: "用户管理", icon: Users }],
      });
    }
    return g;
  }, [user]);

  useLayoutEffect(() => {
    const nav = navRef.current;
    const indicator = indicatorRef.current;
    if (!nav || !indicator) return;

    const activeLink = nav.querySelector<HTMLElement>('[data-nav-active="true"]');
    if (!activeLink) {
      gsap.set(indicator, { opacity: 0 });
      return;
    }

    const navRect = nav.getBoundingClientRect();
    const linkRect = activeLink.getBoundingClientRect();
    const top = linkRect.top - navRect.top + nav.scrollTop;

    if (prefersReducedMotion()) {
      gsap.set(indicator, { top, height: linkRect.height, opacity: 1 });
      return;
    }

    gsap.to(indicator, {
      top,
      height: linkRect.height,
      opacity: 1,
      duration: 0.38,
      ease: "power3.out",
    });
  }, [pathname, groups]);

  return (
    <aside
      className={cn(
        sidebarShellClass,
        "fixed left-0 top-0 z-40 flex h-screen w-[272px] flex-col text-slate-700"
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-blue-100/50 to-transparent" />
      <div className="pointer-events-none absolute -left-10 bottom-24 h-32 w-32 rounded-full bg-emerald-200/30 blur-3xl" />

      {/* 品牌区 — 与首页顶栏一致 */}
      <div className="relative border-b border-white/60 px-5 py-5">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md shadow-blue-500/25">
              <Radar className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 ring-2 ring-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-bold tracking-tight text-slate-800">
              政策智能监测
            </h1>
            <p className="text-[11px] text-slate-400">Policy Intelligence</p>
          </div>
        </Link>
      </div>

      {/* 导航 */}
      <nav
        ref={navRef}
        className="sidebar-scroll relative flex-1 overflow-y-auto px-3 py-4"
      >
        <div
          ref={indicatorRef}
          className="pointer-events-none absolute left-3 right-3 z-0 rounded-xl bg-white/90 shadow-[0_4px_16px_rgba(59,130,246,0.12)] ring-1 ring-blue-100"
          style={{ opacity: 0, top: 0, height: 44 }}
        />

        {groups.map((group) => (
          <div key={group.title} className="mb-6 last:mb-2">
            <div className="mb-2 flex items-center gap-2 px-3">
              <span className="shrink-0 text-[10px] font-bold uppercase tracking-[0.2em] text-blue-500/80">
                {group.title}
              </span>
              <span className="h-px flex-1 bg-gradient-to-r from-slate-200 to-transparent" />
            </div>

            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = isActive(pathname, item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    data-nav-active={active ? "true" : undefined}
                    className={cn(
                      "group relative z-10 flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors duration-200",
                      active
                        ? "text-blue-700"
                        : "text-slate-500 hover:text-slate-800"
                    )}
                  >
                    <span
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-all duration-200",
                        active
                          ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-500/25"
                          : "bg-white/80 text-slate-400 ring-1 ring-slate-200/80 group-hover:bg-blue-50 group-hover:text-blue-600 group-hover:ring-blue-100"
                      )}
                    >
                      {Icon && (
                        <Icon className="h-[15px] w-[15px]" strokeWidth={active ? 2.25 : 2} />
                      )}
                    </span>
                    <span className="flex-1 leading-none">{item.label}</span>
                    {active ? (
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                    ) : (
                      <span className="h-4 w-4 shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
                        <svg viewBox="0 0 16 16" className="h-4 w-4 text-slate-300" fill="none">
                          <path
                            d="M6 4l4 4-4 4"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* 底部 */}
      <div className="relative border-t border-white/60 px-4 py-4">
        <div className={cn(glassPanelClass, "p-3.5")}>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-md shadow-violet-500/20">
              <Sparkles className="h-4 w-4" strokeWidth={2} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-800">DeepSeek AI</p>
              <p className="mt-0.5 text-[10px] text-slate-400">政策解读引擎已连接</p>
            </div>
            <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 ring-1 ring-emerald-100">
              在线
            </span>
          </div>
        </div>
        <p className="mt-3 text-center text-[10px] tracking-wider text-slate-400">
          V1.0 · 教育政策监测平台
        </p>
      </div>
    </aside>
  );
}
