"use client";

import Link from "next/link";
import { useLayoutEffect, useRef, useState, useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { api } from "@/lib/api";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Database,
  Lock,
  MessageSquare,
  Radar,
  Search,
  Sparkles,
} from "lucide-react";
import { ChinaMonitorMap } from "@/components/landing/china-monitor-map";
import { PolicyHeroScene } from "@/components/landing/policy-hero-scene";
import { Button } from "@/components/ui/button";
import { prefersReducedMotion } from "@/lib/gsap-motion";

const navLinks = [
  { href: "#coverage", label: "全国覆盖" },
  { href: "#features", label: "核心能力" },
  { href: "#workflow", label: "使用流程" },
  { href: "#cta", label: "立即开始" },
];

const features = [
  {
    icon: Database,
    title: "智能采集",
    desc: "覆盖全国教育主管部门，按栏目、关键词、时间灵活配置。",
    color: "bg-blue-500",
  },
  {
    icon: Sparkles,
    title: "AI 解读",
    desc: "自动提炼摘要、标签与关键词，快速把握政策脉络。",
    color: "bg-violet-500",
  },
  {
    icon: MessageSquare,
    title: "政策问答",
    desc: "基于个人知识库的智能问答，随时检索相关政策。",
    color: "bg-indigo-500",
  },
  {
    icon: Lock,
    title: "数据隔离",
    desc: "独立账户与配额体系，采集数据互不可见。",
    color: "bg-emerald-500",
  },
];

const steps = [
  { n: "01", title: "注册账户", desc: "免费注册，获得采集与 AI 分析配额" },
  { n: "02", title: "配置采集", desc: "选择省份网站与栏目，一键启动监测" },
  { n: "03", title: "洞察政策", desc: "知识库、AI 解读、全文检索一站完成" },
];

export default function HomePage() {
  const rootRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const heroTextRef = useRef<HTMLDivElement>(null);
  const sceneWrapRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLAnchorElement>(null);
  const [allowSignup, setAllowSignup] = useState(true);

  useEffect(() => {
    api.getAuthConfig()
      .then((cfg) => setAllowSignup(cfg.allow_signup))
      .catch(() => setAllowSignup(true));
  }, []);

  useLayoutEffect(() => {
    if (prefersReducedMotion()) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.from(navRef.current, { y: -28, opacity: 0, duration: 0.65 })
        .from(
          heroTextRef.current?.children ?? [],
          { x: -36, opacity: 0, duration: 0.7, stagger: 0.1 },
          "-=0.35"
        )
        .from(
          sceneWrapRef.current,
          { x: 48, opacity: 0, scale: 0.92, duration: 0.85, ease: "back.out(1.4)" },
          "-=0.55"
        )
        .from("[data-map-image]", { scale: 0.94, opacity: 0, duration: 0.85, ease: "power2.out" }, "-=0.45")
        .from(
          "[data-map-province]",
          { scale: 0, opacity: 0, duration: 0.3, stagger: 0.02, ease: "back.out(2.5)" },
          "-=0.5"
        )
        .from("[data-map-moe]", { scale: 0, opacity: 0, duration: 0.45, ease: "back.out(2)" }, "-=0.15")
        .from("[data-iso-stat]", { y: 12, opacity: 0, duration: 0.4, stagger: 0.08 }, "-=0.2")
        .from("[data-iso-badge], [data-iso-badge-b]", { y: -16, opacity: 0, duration: 0.45, stagger: 0.1 }, "-=0.15");

      // 持续动效 — 3D 地图
      gsap.to("[data-iso-platform]", {
        y: -10,
        duration: 4,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      gsap.to("[data-iso-card]", {
        rotateY: -4,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      gsap.to("[data-map-radar]", {
        scale: 1.2,
        opacity: 0,
        duration: 3,
        repeat: -1,
        ease: "power1.out",
      });

      // 滚动显现
      gsap.utils.toArray<HTMLElement>("[data-scroll-reveal]").forEach((el) => {
        gsap.from(el, {
          scrollTrigger: {
            trigger: el,
            start: "top 88%",
            toggleActions: "play none none none",
          },
          y: 32,
          opacity: 0,
          duration: 0.65,
          ease: "power2.out",
        });
      });
    }, rootRef);

    return () => ctx.revert();
  }, []);

  // CTA 磁吸微交互
  useLayoutEffect(() => {
    const btn = ctaRef.current;
    if (!btn || prefersReducedMotion()) return;

    const onMove = (e: MouseEvent) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      gsap.to(btn, { x: x * 0.18, y: y * 0.18, duration: 0.35, ease: "power2.out" });
    };
    const onLeave = () => gsap.to(btn, { x: 0, y: 0, duration: 0.5, ease: "elastic.out(1, 0.5)" });

    btn.addEventListener("mousemove", onMove);
    btn.addEventListener("mouseleave", onLeave);
    return () => {
      btn.removeEventListener("mousemove", onMove);
      btn.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      className="min-h-screen bg-[#e8eef4] text-slate-800"
      style={{
        backgroundImage:
          "radial-gradient(ellipse 90% 60% at 70% 0%, rgba(147,197,253,0.35), transparent 55%), radial-gradient(ellipse 50% 40% at 10% 80%, rgba(167,243,208,0.25), transparent 50%), linear-gradient(180deg, #eef3f8 0%, #e4ebf3 50%, #dfe8f2 100%)",
      }}
    >
      {/* 顶栏 — 悬浮胶囊 */}
      <div className="sticky top-0 z-50 px-4 pt-5 md:px-8">
        <header
          ref={navRef}
          className="mx-auto flex max-w-6xl items-center justify-between rounded-full border border-white/70 bg-white/85 px-5 py-2.5 shadow-[0_8px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl md:px-8"
        >
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md shadow-blue-500/25">
              <Radar className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-bold tracking-tight text-slate-800">政策智能监测</span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="relative rounded-full px-4 py-2 text-sm font-medium text-slate-500 transition hover:text-blue-600"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-slate-600 hover:text-blue-600">
                {allowSignup ? "登录" : "管理员登录"}
              </Button>
            </Link>
            {allowSignup && (
              <Link href="/register">
                <Button
                  size="sm"
                  className="rounded-full bg-blue-600 px-5 shadow-md shadow-blue-600/25 hover:bg-blue-500"
                >
                  注册
                </Button>
              </Link>
            )}
          </div>
        </header>
      </div>

      {/* Hero — 左右分栏 */}
      <section className="mx-auto grid max-w-7xl items-center gap-4 px-6 pb-16 pt-10 md:grid-cols-2 md:gap-0 md:px-8 md:pt-16 lg:pt-20">
        <div ref={heroTextRef} className="relative z-10 md:pr-4">
          <span className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white shadow-lg shadow-blue-600/30">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
            New Future · 教育政策情报
          </span>

          <h1 className="mt-6 text-4xl font-bold leading-[1.12] tracking-tight text-slate-900 md:text-5xl lg:text-[3.25rem]">
            智能监测
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-indigo-500 bg-clip-text text-transparent">
              政策动态
            </span>
          </h1>

          <p className="mt-5 max-w-md text-base leading-relaxed text-slate-500">
            {allowSignup
              ? "一站式教育政策采集与 AI 分析平台。注册登录即可配置监测任务，数据按账户隔离，管理员统一管控配额。"
              : "一站式教育政策采集与 AI 分析平台。当前为单用户模式，请使用管理员账号登录后使用全部功能。"}
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            {allowSignup ? (
              <>
                <Link
                  ref={ctaRef}
                  href="/register"
                  className="group inline-flex items-center gap-3 rounded-full bg-white py-2 pl-6 pr-2 text-sm font-semibold text-slate-800 shadow-[0_12px_40px_rgba(15,23,42,0.1)] ring-1 ring-slate-200/80 transition hover:shadow-[0_16px_48px_rgba(59,130,246,0.18)] hover:ring-blue-200"
                >
                  免费开始使用
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white transition group-hover:bg-blue-500">
                    <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
                <Link
                  href="/login"
                  className="text-sm font-medium text-slate-500 transition hover:text-blue-600"
                >
                  已有账户登录 →
                </Link>
              </>
            ) : (
              <Link
                ref={ctaRef}
                href="/login"
                className="group inline-flex items-center gap-3 rounded-full bg-white py-2 pl-6 pr-2 text-sm font-semibold text-slate-800 shadow-[0_12px_40px_rgba(15,23,42,0.1)] ring-1 ring-slate-200/80 transition hover:shadow-[0_16px_48px_rgba(59,130,246,0.18)] hover:ring-blue-200"
              >
                管理员登录
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white transition group-hover:bg-blue-500">
                  <ArrowRight className="h-4 w-4" />
                </span>
              </Link>
            )}
          </div>

          {/* 迷你指标 */}
          <div className="mt-10 flex flex-wrap gap-6 border-t border-slate-300/40 pt-8">
            {[
              { v: "32+", l: "省级监测源" },
              { v: "AI", l: "深度解读" },
              { v: "100%", l: "数据隔离" },
            ].map((s) => (
              <div key={s.l}>
                <p className="text-xl font-bold text-slate-800">{s.v}</p>
                <p className="text-xs text-slate-400">{s.l}</p>
              </div>
            ))}
          </div>
        </div>

        <div ref={sceneWrapRef} className="relative -mr-4 flex justify-center overflow-visible md:-mr-8 md:justify-end lg:-mr-12">
          <PolicyHeroScene className="w-[115%] max-w-none md:w-[125%]" />
        </div>
      </section>

      {/* 全国覆盖地图 */}
      <section id="coverage" className="mx-auto max-w-6xl px-6 py-12 md:px-8">
        <div data-scroll-reveal className="mb-8 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-emerald-600">Nationwide</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">全国政策监测覆盖</h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-500">
            教育部与 31 个省级教育主管部门官网同步监测，绿点即为已接入监测源
          </p>
        </div>
        <div data-scroll-reveal>
          <ChinaMonitorMap variant="section" showLabels interactive className="mx-auto w-full max-w-6xl" />
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-amber-500 ring-2 ring-white" /> 国家级（教育部）
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-emerald-500 ring-2 ring-white" /> 省级教育厅
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-blue-400/40 ring-2 ring-blue-200" /> 雷达扫描范围
            </span>
          </div>
        </div>
      </section>

      {/* 核心能力 */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20 md:px-8">
        <div data-scroll-reveal className="mb-12 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-500">Capabilities</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">核心能力</h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                data-scroll-reveal
                className="group rounded-3xl border border-white/80 bg-white/70 p-6 shadow-[0_8px_32px_rgba(15,23,42,0.06)] backdrop-blur-sm transition hover:-translate-y-1 hover:shadow-[0_16px_48px_rgba(59,130,246,0.12)]"
              >
                <div
                  className={`mb-4 flex h-11 w-11 items-center justify-center rounded-2xl ${f.color} text-white shadow-lg`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-800">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">{f.desc}</p>
              </div>
            );
          })}
        </div>

        <div
          data-scroll-reveal
          className="mt-6 flex flex-wrap items-center justify-center gap-8 rounded-3xl border border-white/80 bg-white/50 px-8 py-6 shadow-sm backdrop-blur-sm"
        >
          {[
            { icon: BookOpen, label: "政策知识库" },
            { icon: Search, label: "全文检索" },
            { icon: BarChart3, label: "数据分析" },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="flex items-center gap-2 text-sm font-medium text-slate-600">
                <Icon className="h-4 w-4 text-blue-500" />
                {item.label}
              </div>
            );
          })}
        </div>
      </section>

      {/* 流程 */}
      <section id="workflow" className="mx-auto max-w-6xl px-6 py-12 md:px-8">
        <div data-scroll-reveal className="mb-10 text-center">
          <h2 className="text-2xl font-bold text-slate-900">三步开启监测</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {steps.map((s) => (
            <div
              key={s.n}
              data-scroll-reveal
              className="rounded-3xl border border-white/80 bg-white/60 p-6 shadow-[0_6px_24px_rgba(15,23,42,0.05)] backdrop-blur-sm"
            >
              <span className="text-4xl font-bold text-blue-100">{s.n}</span>
              <h3 className="mt-1 font-semibold text-slate-800">{s.title}</h3>
              <p className="mt-2 text-sm text-slate-500">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section id="cta" className="mx-auto max-w-6xl px-6 pb-24 md:px-8">
        <div
          data-scroll-reveal
          className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-blue-600 via-blue-600 to-indigo-600 px-8 py-14 text-center text-white shadow-[0_24px_64px_rgba(37,99,235,0.35)]"
        >
          <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <h2 className="relative text-2xl font-bold md:text-3xl">构建你的专属政策情报库</h2>
          <p className="relative mx-auto mt-3 max-w-md text-blue-100">
            {allowSignup
              ? "立即注册，登录后进入采集系统。每位用户数据独立隔离，安全可控。"
              : "系统当前为单用户模式，请使用管理员账号登录进入采集系统。"}
          </p>
          <Link
            href={allowSignup ? "/register" : "/login"}
            className="relative mt-8 inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-blue-600 shadow-xl transition hover:bg-blue-50"
          >
            {allowSignup ? "创建免费账户" : "管理员登录"}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-300/30 py-8 text-center text-xs text-slate-400">
        © 2026 教育政策智能监测平台 · Policy Intelligence
      </footer>
    </div>
  );
}
