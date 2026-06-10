/** 各省会经纬度（教育厅官网所在地） */
export type ProvinceGeo = {
  id: string;
  name: string;
  lng: number;
  lat: number;
  hub?: true;
};

export const PROVINCE_GEO: ProvinceGeo[] = [
  { id: "xj", name: "新疆", lng: 87.62, lat: 43.82 },
  { id: "xz", name: "西藏", lng: 91.11, lat: 29.65 },
  { id: "qh", name: "青海", lng: 101.78, lat: 36.62 },
  { id: "gs", name: "甘肃", lng: 103.82, lat: 36.06 },
  { id: "nx", name: "宁夏", lng: 106.23, lat: 38.49 },
  { id: "nmg", name: "内蒙古", lng: 111.67, lat: 40.82 },
  { id: "hlj", name: "黑龙江", lng: 126.63, lat: 45.75 },
  { id: "jl", name: "吉林", lng: 125.32, lat: 43.9 },
  { id: "ln", name: "辽宁", lng: 123.43, lat: 41.8 },
  { id: "bj", name: "北京", lng: 116.41, lat: 39.9, hub: true },
  { id: "tj", name: "天津", lng: 117.2, lat: 39.13 },
  { id: "heb", name: "河北", lng: 114.52, lat: 38.05 },
  { id: "sx", name: "山西", lng: 112.55, lat: 37.87 },
  { id: "sd", name: "山东", lng: 117.12, lat: 36.65 },
  { id: "snx", name: "陕西", lng: 108.95, lat: 34.27 },
  { id: "hen", name: "河南", lng: 113.63, lat: 34.75 },
  { id: "hub", name: "湖北", lng: 114.31, lat: 30.59 },
  { id: "ah", name: "安徽", lng: 117.28, lat: 31.86 },
  { id: "js", name: "江苏", lng: 118.78, lat: 32.06 },
  { id: "sh", name: "上海", lng: 121.47, lat: 31.23 },
  { id: "zj", name: "浙江", lng: 120.15, lat: 30.28 },
  { id: "jx", name: "江西", lng: 115.89, lat: 28.68 },
  { id: "hun", name: "湖南", lng: 112.98, lat: 28.2 },
  { id: "cq", name: "重庆", lng: 106.55, lat: 29.56 },
  { id: "sc", name: "四川", lng: 104.07, lat: 30.67 },
  { id: "gz", name: "贵州", lng: 106.71, lat: 26.57 },
  { id: "yn", name: "云南", lng: 102.83, lat: 24.88 },
  { id: "fj", name: "福建", lng: 119.3, lat: 26.08 },
  { id: "gd", name: "广东", lng: 113.26, lat: 23.13 },
  { id: "gx", name: "广西", lng: 108.37, lat: 22.82 },
  { id: "han", name: "海南", lng: 110.33, lat: 20.02 },
];

/**
 * 针对当前 3D 浮雕底图的手动锚点：(经度, 纬度) → 图像百分比 (x%, y%)
 * 用最小二乘拟合仿射变换，适配透视变形。
 */
const CALIBRATION_ANCHORS: [lng: number, lat: number, x: number, y: number][] = [
  [87.6, 43.8, 19, 27], // 新疆
  [91.1, 29.7, 25, 43], // 西藏
  [101.8, 36.6, 33, 34], // 青海
  [104.1, 30.7, 41, 45], // 四川
  [108.9, 34.3, 49, 38], // 陕西
  [116.4, 39.9, 57, 30], // 北京
  [113.3, 23.1, 59, 60], // 广东
  [119.3, 26.1, 66, 52], // 福建
  [121.5, 31.2, 70, 40], // 上海
  [126.6, 45.8, 77, 15], // 黑龙江
  [110.3, 20.0, 61, 73], // 海南
];

function lstsq3(
  rows: [number, number, number][],
  targets: number[],
): [number, number, number] {
  const n = 3;
  const ata = Array.from({ length: n }, () => Array(n).fill(0));
  const atb = Array(n).fill(0);
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const t = targets[i];
    for (let r = 0; r < n; r++) {
      atb[r] += row[r] * t;
      for (let c = 0; c < n; c++) ata[r][c] += row[r] * row[c];
    }
  }
  const aug = ata.map((r, i) => [...r, atb[i]]);
  for (let col = 0; col < n; col++) {
    let pivot = col;
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(aug[r][col]) > Math.abs(aug[pivot][col])) pivot = r;
    }
    [aug[col], aug[pivot]] = [aug[pivot], aug[col]];
    for (let r = col + 1; r < n; r++) {
      const factor = aug[r][col] / aug[col][col];
      for (let j = col; j <= n; j++) aug[r][j] -= factor * aug[col][j];
    }
  }
  const result = Array(n).fill(0);
  for (let i = n - 1; i >= 0; i--) {
    result[i] =
      (aug[i][n] - aug[i].slice(i + 1, n).reduce((s, v, j) => s + v * result[i + 1 + j], 0)) /
      aug[i][i];
  }
  return result as [number, number, number];
}

const anchorRows = CALIBRATION_ANCHORS.map(([lng, lat]) => [lng, lat, 1] as [number, number, number]);
const AFFINE_X = lstsq3(
  anchorRows,
  CALIBRATION_ANCHORS.map(([, , x]) => x),
);
const AFFINE_Y = lstsq3(
  anchorRows,
  CALIBRATION_ANCHORS.map(([, , , y]) => y),
);

export function projectLngLat(lng: number, lat: number): { x: number; y: number } {
  const x = lng * AFFINE_X[0] + lat * AFFINE_X[1] + AFFINE_X[2];
  const y = lng * AFFINE_Y[0] + lat * AFFINE_Y[1] + AFFINE_Y[2];
  return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
}

export type ProvinceNode = ProvinceGeo & { x: number; y: number };

/** 由经纬度 + 锚点仿射变换生成的默认标点 */
export function buildProjectedNodes(): ProvinceNode[] {
  return PROVINCE_GEO.map((p) => {
    const { x, y } = projectLngLat(p.lng, p.lat);
    return { ...p, x, y };
  });
}

export const CALIBRATION_STORAGE_KEY = "china-map-marker-calibration";
