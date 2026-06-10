"use client";

import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { Activity, MapPin, Radar } from "lucide-react";
import { ChinaMonitorMap } from "./china-monitor-map";
import { prefersReducedMotion } from "@/lib/gsap-motion";

/** 3D 浮雕中国地图 Hero — 无边框大图 */
export function PolicyHeroScene({ className = "" }: { className?: string }) {
  const tiltRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const wrap = tiltRef.current;
    const map = mapRef.current;
    if (!wrap || !map || prefersReducedMotion()) return;

    const onMove = (e: MouseEvent) => {
      const rect = wrap.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      gsap.to(map, {
        rotateX: 4 - y * 8,
        rotateY: -6 + x * 12,
        duration: 0.6,
        ease: "power2.out",
      });
    };
    const onLeave = () =>
      gsap.to(map, { rotateX: 4, rotateY: -6, duration: 0.8, ease: "elastic.out(1, 0.6)" });

    wrap.addEventListener("mousemove", onMove);
    wrap.addEventListener("mouseleave", onLeave);
    return () => {
      wrap.removeEventListener("mousemove", onMove);
      wrap.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div className={`relative w-full max-w-[780px] ${className}`}>
      <div
        ref={tiltRef}
        data-iso-platform
        className="relative"
        style={{ perspective: "1600px" }}
      >
        <div
          ref={mapRef}
          data-iso-card
          className="relative"
          style={{ transform: "rotateX(4deg) rotateY(-6deg)", transformStyle: "preserve-3d" }}
        >
          <ChinaMonitorMap variant="hero" interactive />
        </div>
      </div>

      {/* 浮动信息 — 不框住地图 */}
      <div
        data-iso-badge
        className="absolute left-0 top-[4%] z-20 rounded-2xl border border-slate-300/40 bg-slate-900/[0.04] px-4 py-3 shadow-lg backdrop-blur-md"
      >
        <p className="text-[10px] font-bold uppercase tracking-wider text-blue-500">Monitor</p>
        <p className="text-lg font-bold text-slate-800">32+ 源站</p>
      </div>

      <div
        data-iso-badge-b
        className="absolute bottom-[8%] right-0 z-20 flex items-center gap-3"
      >
        {[
          { icon: MapPin, label: "省级", value: "31" },
          { icon: Radar, label: "国家级", value: "1" },
          { icon: Activity, label: "覆盖", value: "100%" },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.label}
              data-iso-stat
              className="rounded-xl border border-slate-300/40 bg-slate-900/[0.04] px-3 py-2 text-center shadow-md backdrop-blur-md"
            >
              <Icon className="mx-auto h-3.5 w-3.5 text-blue-500" />
              <p className="text-xs font-bold text-slate-800">{s.value}</p>
              <p className="text-[9px] text-slate-400">{s.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
