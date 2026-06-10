"use client";

import { useLayoutEffect, useRef, useState, useEffect } from "react";
import gsap from "gsap";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fadeUp } from "@/lib/gsap-motion";

export default function LoginPage() {
  const cardRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [authConfig, setAuthConfig] = useState<{
    multi_user_enabled: boolean;
    allow_signup: boolean;
    allow_public_login: boolean;
  } | null>(null);

  useEffect(() => {
    api.getAuthConfig().then(setAuthConfig).catch(() => {
      setAuthConfig({
        multi_user_enabled: true,
        allow_signup: true,
        allow_public_login: true,
      });
    });
  }, []);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => fadeUp(cardRef.current, { y: 24, duration: 0.55 }));
    return () => ctx.revert();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { access_token } = await api.login(username, password);
      setToken(access_token);
      router.push("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "用户名或密码错误");
    } finally {
      setLoading(false);
    }
  };

  const singleUserMode = authConfig && !authConfig.allow_public_login;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 via-white to-slate-100">
      <div ref={cardRef} className="w-full max-w-md">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">教育政策智能监测平台</CardTitle>
            <p className="mt-2 text-sm text-slate-500">
              {singleUserMode
                ? "系统已关闭多用户模式，请使用管理员账号登录"
                : "登录以访问采集系统与 AI 解读服务"}
            </p>
            {authConfig?.allow_signup && (
              <p className="mt-1 text-xs text-slate-400">
                还没有账户？{" "}
                <a href="/register" className="text-primary-600 hover:underline">
                  免费注册
                </a>
              </p>
            )}
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">用户名</label>
                <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">密码</label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "登录中..." : "登 录"}
              </Button>
            </form>
            {singleUserMode ? (
              <p className="mt-4 text-center text-xs text-slate-400">单用户模式 · 仅管理员可登录</p>
            ) : (
              <p className="mt-4 text-center text-xs text-slate-400">默认账号 admin / admin123</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
