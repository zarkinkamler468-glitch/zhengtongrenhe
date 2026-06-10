"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { getDefaultProvinceNodes, getProvinceNodes, type ProvinceNode } from "@/lib/china-map-nodes";
import { MapMarker } from "./map-marker";

export type { ProvinceNode };
export { getProvinceNodes as getMonitorMapNodes };

type ChinaMonitorMapProps = {
  className?: string;
  variant?: "hero" | "section";
  showLabels?: boolean;
  interactive?: boolean;
};

export function ChinaMonitorMap({
  className = "",
  variant = "hero",
  showLabels = false,
  interactive = true,
}: ChinaMonitorMapProps) {
  const [nodes, setNodes] = useState<ProvinceNode[]>(getDefaultProvinceNodes);
  const [active, setActive] = useState<string | null>(null);
  const isHero = variant === "hero";

  useEffect(() => {
    setNodes(getProvinceNodes());
  }, []);

  const moe = nodes.find((p) => p.hub);
  const provinces = nodes.filter((p) => !p.hub);

  return (
    <div
      className={`relative select-none ${className}`}
      data-china-map
      aria-label="全国教育政策监测 3D 地形图"
      role="img"
    >
      <div className={`relative ${isHero ? "scale-[1.12] md:scale-[1.18]" : "scale-105 md:scale-110"}`}>
        <Image
          src="/images/china-relief-3d.png"
          alt="中国 3D 地形监测地图"
          width={1024}
          height={682}
          className="h-auto w-full object-contain drop-shadow-[0_28px_56px_rgba(15,23,42,0.18)]"
          priority={isHero}
          data-map-image
        />

        <div className="absolute inset-0">
          {moe && (
            <div
              className="pointer-events-none absolute"
              style={{ left: `${moe.x}%`, top: `${moe.y}%`, transform: "translate(-50%, -50%)" }}
            >
              <div
                data-map-radar
                className="absolute h-16 w-16 -translate-x-1/2 -translate-y-[calc(50%+10px)] rounded-full border border-amber-400/20"
              />
            </div>
          )}

          {moe && (
            <button
              type="button"
              data-map-moe
              className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 transition-transform duration-200 ${
                active === moe.id ? "scale-105" : "scale-100"
              }`}
              style={{ left: `${moe.x}%`, top: `${moe.y}%` }}
              onMouseEnter={() => interactive && setActive(moe.id)}
              onMouseLeave={() => interactive && setActive(null)}
            >
              <MapMarker
                variant="hub"
                size={variant}
                name="教育部"
                showLabel={showLabels || active === moe.id}
              />
            </button>
          )}

          {provinces.map((p, i) => (
            <button
              key={p.id}
              type="button"
              data-map-province
              className={`absolute z-10 -translate-x-1/2 -translate-y-1/2 transition-transform duration-200 ${
                active === p.id ? "scale-105" : "scale-100"
              }`}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              onMouseEnter={() => interactive && setActive(p.id)}
              onMouseLeave={() => interactive && setActive(null)}
            >
              <MapMarker
                variant="province"
                size={variant}
                name={p.name}
                showLabel={showLabels || active === p.id}
                floatIndex={i}
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
