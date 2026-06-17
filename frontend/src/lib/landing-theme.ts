import type { CSSProperties } from "react";

/** 与首页一致的背景与玻璃卡片样式，供后台各页面复用 */

export const landingBackgroundClass = "min-h-screen bg-[#e8eef4] text-slate-800";

export const landingBackgroundStyle: CSSProperties = {
  backgroundImage:
    "radial-gradient(ellipse 90% 60% at 70% 0%, rgba(147,197,253,0.35), transparent 55%), radial-gradient(ellipse 50% 40% at 10% 80%, rgba(167,243,208,0.25), transparent 50%), linear-gradient(180deg, #eef3f8 0%, #e4ebf3 50%, #dfe8f2 100%)",
};

export const glassCardClass =
  "rounded-2xl border border-white/80 bg-white/75 shadow-[0_8px_32px_rgba(15,23,42,0.06)] backdrop-blur-sm";

export const glassPanelClass =
  "rounded-3xl border border-white/80 bg-white/70 shadow-[0_8px_32px_rgba(15,23,42,0.06)] backdrop-blur-sm";

export const capsuleHeaderClass =
  "rounded-full border border-white/70 bg-white/85 shadow-[0_8px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl";

export const pageEyebrowClass =
  "text-xs font-bold uppercase tracking-[0.25em] text-blue-500";

export const sidebarShellClass =
  "border-r border-white/70 bg-white/75 shadow-[4px_0_32px_rgba(15,23,42,0.06)] backdrop-blur-xl";
