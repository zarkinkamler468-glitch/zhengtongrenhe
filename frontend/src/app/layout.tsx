import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "教育政策智能监测平台",
  description: "自动监测教育政策、AI解读分析",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
