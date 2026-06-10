import { buildProjectedNodes, CALIBRATION_STORAGE_KEY, type ProvinceNode } from "./china-map-geo";

export { CALIBRATION_STORAGE_KEY, type ProvinceNode };

/** 针对 3D 浮雕底图手绘校准后的标点坐标 */
export const PROVINCE_NODES: ProvinceNode[] = [
  { id: "xj", name: "新疆", lng: 87.62, lat: 43.82, x: 24.3, y: 29.9 },
  { id: "xz", name: "西藏", lng: 91.11, lat: 29.65, x: 23.4, y: 51.3 },
  { id: "qh", name: "青海", lng: 101.78, lat: 36.62, x: 36.1, y: 43.4 },
  { id: "gs", name: "甘肃", lng: 103.82, lat: 36.06, x: 41.7, y: 35.9 },
  { id: "nx", name: "宁夏", lng: 106.23, lat: 38.49, x: 48.8, y: 44.3 },
  { id: "nmg", name: "内蒙古", lng: 111.67, lat: 40.82, x: 56.4, y: 32.6 },
  { id: "hlj", name: "黑龙江", lng: 126.63, lat: 45.75, x: 82.2, y: 18.7 },
  { id: "jl", name: "吉林", lng: 125.32, lat: 43.9, x: 78.3, y: 25.2 },
  { id: "ln", name: "辽宁", lng: 123.43, lat: 41.8, x: 73, y: 28.7 },
  { id: "bj", name: "北京", lng: 116.41, lat: 39.9, x: 66.4, y: 37.2, hub: true },
  { id: "tj", name: "天津", lng: 117.2, lat: 39.13, x: 68.6, y: 40 },
  { id: "heb", name: "河北", lng: 114.52, lat: 38.05, x: 63, y: 37.3 },
  { id: "sx", name: "山西", lng: 112.55, lat: 37.87, x: 58.5, y: 41.7 },
  { id: "sd", name: "山东", lng: 117.12, lat: 36.65, x: 71, y: 42.6 },
  { id: "snx", name: "陕西", lng: 108.95, lat: 34.27, x: 53.8, y: 44.4 },
  { id: "hen", name: "河南", lng: 113.63, lat: 34.75, x: 64.7, y: 47.8 },
  { id: "hub", name: "湖北", lng: 114.31, lat: 30.59, x: 60.5, y: 54.7 },
  { id: "ah", name: "安徽", lng: 117.28, lat: 31.86, x: 69.5, y: 52.2 },
  { id: "js", name: "江苏", lng: 118.78, lat: 32.06, x: 73.6, y: 48.1 },
  { id: "sh", name: "上海", lng: 121.47, lat: 31.23, x: 76.3, y: 51.9 },
  { id: "zj", name: "浙江", lng: 120.15, lat: 30.28, x: 75.1, y: 56.7 },
  { id: "jx", name: "江西", lng: 115.89, lat: 28.68, x: 65.5, y: 63.2 },
  { id: "hun", name: "湖南", lng: 112.98, lat: 28.2, x: 60.1, y: 61.1 },
  { id: "cq", name: "重庆", lng: 106.55, lat: 29.56, x: 52.8, y: 53.9 },
  { id: "sc", name: "四川", lng: 104.07, lat: 30.67, x: 45.4, y: 53.7 },
  { id: "gz", name: "贵州", lng: 106.71, lat: 26.57, x: 53.4, y: 62.3 },
  { id: "yn", name: "云南", lng: 102.83, lat: 24.88, x: 41.5, y: 68.2 },
  { id: "fj", name: "福建", lng: 119.3, lat: 26.08, x: 71.5, y: 65.5 },
  { id: "gd", name: "广东", lng: 113.26, lat: 23.13, x: 63.7, y: 73 },
  { id: "gx", name: "广西", lng: 108.37, lat: 22.82, x: 53, y: 70.3 },
  { id: "han", name: "海南", lng: 110.33, lat: 20.02, x: 55.9, y: 83.9 },
];

function readCalibrationOverrides(): Record<string, { x: number; y: number }> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CALIBRATION_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Record<string, { x: number; y: number }>;
  } catch {
    return null;
  }
}

function applyOverrides(nodes: ProvinceNode[]): ProvinceNode[] {
  const overrides = readCalibrationOverrides();
  if (!overrides) return nodes;
  return nodes.map((n) => {
    const o = overrides[n.id];
    return o ? { ...n, x: o.x, y: o.y } : n;
  });
}

/** 获取最终用于渲染的监测点坐标 */
export function getProvinceNodes(): ProvinceNode[] {
  return applyOverrides(PROVINCE_NODES);
}

export function getDefaultProvinceNodes(): ProvinceNode[] {
  return PROVINCE_NODES;
}

/** 地理投影结果，供校准页「重置为地理投影」使用 */
export function getProjectedProvinceNodes(): ProvinceNode[] {
  return buildProjectedNodes();
}
