import type { Metadata } from "next";
import { ChunkErrorRecovery } from "@/components/chunk-error-recovery";
import "./globals.css";

export const metadata: Metadata = {
  title: "教育政策智能监测平台",
  description: "自动监测教育政策、AI解读分析",
};

/** 禁止静态预渲染长期缓存 HTML，避免部署后 CSS/chunk 404 导致整页错乱 */
export const dynamic = "force-dynamic";
export const revalidate = 0;
export const fetchCache = "force-no-store";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <ChunkErrorRecovery />
        {children}
      </body>
    </html>
  );
}
