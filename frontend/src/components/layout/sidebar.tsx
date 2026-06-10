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
  }, [pathname]);

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[272px] flex-col border-r border-white/[0.06] bg-[#0b1120] text-slate-300 shadow-[4px_0_24px_rgba(0,0,0,0.18)]">
      {/* 氛围光 */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-56 bg-gradient-to-b from-blue-500/[0.07] via-indigo-500/[0.03] to-transparent" />
      <div className="pointer-events-none absolute -left-16 top-24 h-48 w-48 rounded-full bg-blue-600/[0.12] blur-3xl" />
      <div className="pointer-events-none absolute -right-8 bottom-32 h-32 w-32 rounded-full bg-violet-600/[0.08] blur-3xl" />

      {/* 品牌区 */}
      <div className="relative border-b border-white/[0.06] px-5 py-6">
        <div className="flex items-center gap-3.5">
          <div className="relative">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 shadow-lg shadow-blue-600/30 ring-1 ring-white/15">
              <Radar className="h-5 w-5 text-white" strokeWidth={2.25} />
            </div>
            <span className="absolute -right-0.5 -top-0.5 flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-400 ring-2 ring-[#0b1120]" />
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-[15px] font-semibold tracking-tight text-white">
              教育政策智能监测
            </h1>
            <p className="mt-1 text-[11px] font-medium tracking-wide text-slate-500">
              Policy Intelligence · Pro
            </p>
          </div>
        </div>
      </div>

      {/* 导航 */}
      <nav
        ref={navRef}
        className="sidebar-scroll relative flex-1 overflow-y-auto px-3.5 py-5"
      >
        <div
          ref={indicatorRef}
          className="pointer-events-none absolute left-3.5 right-3.5 z-0 rounded-xl bg-gradient-to-r from-blue-500/20 via-indigo-500/10 to-blue-500/[0.02] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] ring-1 ring-blue-400/20"
          style={{ opacity: 0, top: 0, height: 44 }}
        />

        {groups.map((group) => (
          <div key={group.title} className="mb-7 last:mb-2">
            <div className="mb-2.5 flex items-center gap-2.5 px-3">
              <span className="shrink-0 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-600">
                {group.title}
              </span>
              <span className="h-px flex-1 bg-gradient-to-r from-slate-700/90 via-slate-800/40 to-transparent" />
            </div>

            <div className="space-y-1">
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
                      active ? "text-white" : "text-slate-400 hover:text-slate-100"
                    )}
                  >
                    <span
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-all duration-200",
                        active
                          ? "bg-gradient-to-br from-blue-400/25 to-indigo-500/15 text-blue-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] ring-1 ring-blue-400/25"
                          : "bg-white/[0.04] text-slate-500 ring-1 ring-white/[0.04] group-hover:bg-white/[0.07] group-hover:text-slate-300 group-hover:ring-white/[0.08]"
                      )}
                    >
                      {Icon && (
                        <Icon className="h-[15px] w-[15px]" strokeWidth={active ? 2.25 : 2} />
                      )}
                    </span>
                    <span className="flex-1 leading-none">{item.label}</span>
                    {active ? (
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]" />
                    ) : (
                      <span className="h-4 w-4 shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
                        <svg viewBox="0 0 16 16" className="h-4 w-4 text-slate-600" fill="none">
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
      <div className="relative border-t border-white/[0.06] px-4 py-4">
        <div className="rounded-2xl bg-gradient-to-br from-white/[0.05] to-white/[0.02] p-3.5 ring-1 ring-white/[0.07] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-blue-500/15 ring-1 ring-violet-400/20">
              <Sparkles className="h-4 w-4 text-violet-300" strokeWidth={2} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-200">DeepSeek AI</p>
              <p className="mt-0.5 text-[10px] text-slate-500">政策解读引擎已连接</p>
            </div>
            <span className="shrink-0 rounded-lg bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-400 ring-1 ring-emerald-500/25">
              在线
            </span>
          </div>
        </div>
        <p className="mt-3 text-center text-[10px] tracking-wider text-slate-600">V1.0 · 教育政策监测平台</p>
      </div>
    </aside>
  );
}
