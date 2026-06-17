"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { landingBackgroundClass, landingBackgroundStyle } from "@/lib/landing-theme";
import { Header } from "./header";
import { Sidebar } from "./sidebar";

const titles: Record<string, string> = {
  "/dashboard": "数据概览",
  "/admin": "用户管理",
  "/articles": "政策知识库",
  "/search": "全文检索",
  "/monitor": "数据采集中心",
  "/subscriptions": "关键词订阅",
  "/qa": "AI 政策问答",
  "/analytics": "数据分析",
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  const title =
    Object.entries(titles).find(([k]) => pathname === k || pathname.startsWith(k + "/"))?.[1] ||
    "教育政策监测";

  return (
    <div className={landingBackgroundClass} style={landingBackgroundStyle}>
      <Sidebar />
      <div className="ml-[272px] min-h-screen">
        <Header title={title} />
        <main className="px-8 pb-10 pt-2">{children}</main>
      </div>
    </div>
  );
}
