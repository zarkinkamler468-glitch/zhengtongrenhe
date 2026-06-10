"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useMemo, useRef, useState } from "react";
import {
  CALIBRATION_STORAGE_KEY,
  getDefaultProvinceNodes,
  getProjectedProvinceNodes,
  type ProvinceNode,
} from "@/lib/china-map-nodes";
import { projectLngLat, PROVINCE_GEO } from "@/lib/china-map-geo";

const anchors = [
  [87.6, 43.8, 19, 27],
  [91.1, 29.7, 25, 43],
  [101.8, 36.6, 33, 34],
  [104.1, 30.7, 41, 45],
  [108.9, 34.3, 49, 38],
  [116.4, 39.9, 57, 30],
  [113.3, 23.1, 59, 60],
  [119.3, 26.1, 66, 52],
  [121.5, 31.2, 70, 40],
  [126.6, 45.8, 77, 15],
  [110.3, 20.0, 61, 73],
];

export default function MapCalibratePage() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<ProvinceNode[]>(() => {
    if (typeof window === "undefined") return getDefaultProvinceNodes();
    try {
      const raw = localStorage.getItem(CALIBRATION_STORAGE_KEY);
      if (raw) {
        const overrides = JSON.parse(raw) as Record<string, { x: number; y: number }>;
        return getDefaultProvinceNodes().map((n) =>
          overrides[n.id] ? { ...n, ...overrides[n.id] } : n,
        );
      }
    } catch {
      /* ignore */
    }
    return getDefaultProvinceNodes();
  });
  const [dragging, setDragging] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selected) ?? null,
    [nodes, selected],
  );

  const updateFromPointer = useCallback(
    (clientX: number, clientY: number, id: string) => {
      const el = mapRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = Math.round(((clientX - rect.left) / rect.width) * 1000) / 10;
      const y = Math.round(((clientY - rect.top) / rect.height) * 1000) / 10;
      setNodes((prev) =>
        prev.map((n) =>
          n.id === id
            ? { ...n, x: Math.min(98, Math.max(2, x)), y: Math.min(98, Math.max(2, y)) }
            : n,
        ),
      );
    },
    [],
  );

  const onPointerDown = (id: string) => (e: React.PointerEvent) => {
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    setDragging(id);
    setSelected(id);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragging) return;
    updateFromPointer(e.clientX, e.clientY, dragging);
  };

  const onPointerUp = () => setDragging(null);

  const saveLocal = () => {
    const overrides = Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }]));
    localStorage.setItem(CALIBRATION_STORAGE_KEY, JSON.stringify(overrides));
    alert("已保存到浏览器 localStorage，刷新首页即可生效");
  };

  const resetProjection = () => setNodes(getProjectedProvinceNodes());

  const clearSaved = () => {
    localStorage.removeItem(CALIBRATION_STORAGE_KEY);
    setNodes(getDefaultProvinceNodes());
    alert("已清除本地校准，恢复默认坐标");
  };

  const exportTs = () => {
    const lines = nodes.map((n) => {
      const hub = n.hub ? ", hub: true" : "";
      return `  { id: "${n.id}", name: "${n.name}", x: ${n.x}, y: ${n.y}${hub} },`;
    });
    const text = `export const PROVINCE_NODES = [\n${lines.join("\n")}\n];`;
    void navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#e8eef4] px-4 py-6 md:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">地图标点校准工具</h1>
            <p className="mt-1 text-sm text-slate-500">
              拖拽绿点/金点对齐省份位置，保存后首页自动读取。也可复制代码写入项目。
            </p>
          </div>
          <Link href="/" className="text-sm text-blue-600 hover:underline">
            ← 返回首页
          </Link>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={saveLocal}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            保存到本地（立即生效）
          </button>
          <button
            type="button"
            onClick={exportTs}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {copied ? "已复制" : "复制 TS 代码"}
          </button>
          <button
            type="button"
            onClick={resetProjection}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
          >
            重置为地理投影
          </button>
          <button
            type="button"
            onClick={clearSaved}
            className="rounded-lg border border-red-200 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
          >
            清除本地校准
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <div
            ref={mapRef}
            className="relative touch-none select-none"
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
          >
            <Image
              src="/images/china-relief-3d.png"
              alt="校准底图"
              width={1024}
              height={682}
              className="h-auto w-full object-contain"
              draggable={false}
            />
            {nodes.map((n) => (
              <button
                key={n.id}
                type="button"
                onPointerDown={onPointerDown(n.id)}
                onClick={() => setSelected(n.id)}
                className={`absolute z-10 -translate-x-1/2 -translate-y-1/2 cursor-grab active:cursor-grabbing ${
                  selected === n.id ? "z-20" : ""
                }`}
                style={{ left: `${n.x}%`, top: `${n.y}%` }}
              >
                <span
                  className={`block rounded-full ring-2 ring-white ${
                    n.hub
                      ? "h-4 w-4 bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.9)]"
                      : "h-3 w-3 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"
                  } ${selected === n.id ? "scale-125" : ""}`}
                />
                <span className="pointer-events-none absolute left-1/2 top-full mt-0.5 -translate-x-1/2 whitespace-nowrap text-[9px] font-medium text-slate-700">
                  {n.name}
                </span>
              </button>
            ))}
          </div>

          <aside className="rounded-2xl border border-slate-200 bg-white/80 p-4 text-sm shadow-sm">
            <h2 className="font-semibold text-slate-800">选中省份</h2>
            {selectedNode ? (
              <dl className="mt-3 space-y-2 text-slate-600">
                <div className="flex justify-between">
                  <dt>名称</dt>
                  <dd className="font-medium text-slate-900">{selectedNode.name}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>x%</dt>
                  <dd>{selectedNode.x}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>y%</dt>
                  <dd>{selectedNode.y}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>经纬度</dt>
                  <dd>
                    {selectedNode.lng}, {selectedNode.lat}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>地理投影</dt>
                  <dd>
                    {(() => {
                      const p = projectLngLat(selectedNode.lng, selectedNode.lat);
                      return `${p.x}, ${p.y}`;
                    })()}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-3 text-slate-400">点击或拖拽地图上的标点</p>
            )}

            <h2 className="mt-6 font-semibold text-slate-800">原理说明</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-slate-500">
              <li>各省会使用经纬度，通过仿射变换映射到图像百分比</li>
              <li>3D 浮雕图有透视，已用 {anchors.length} 个锚点拟合</li>
              <li>仍不准时可拖拽微调，保存到 localStorage</li>
            </ul>

            <h2 className="mt-6 font-semibold text-slate-800">锚点参考</h2>
            <ul className="mt-2 max-h-40 overflow-y-auto text-xs text-slate-500">
              {PROVINCE_GEO.filter((p) =>
                ["新疆", "西藏", "青海", "四川", "陕西", "北京", "广东", "福建", "上海", "黑龙江", "海南"].includes(
                  p.name,
                ),
              ).map((p) => (
                <li key={p.id}>
                  {p.name}: {projectLngLat(p.lng, p.lat).x}%, {projectLngLat(p.lng, p.lat).y}%
                </li>
              ))}
            </ul>
          </aside>
        </div>
      </div>
    </div>
  );
}
