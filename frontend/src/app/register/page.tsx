"use client";

import Link from "next/link";
import { useLayoutEffect, useRef, useState, useEffect } from "react";
import gsap from "gsap";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fadeUp } from "@/lib/gsap-motion";

export default function RegisterPage() {
  const cardRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    full_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    api.getAuthConfig()
      .then((cfg) => {
        if (!cfg.allow_signup) {
          setBlocked(true);
          router.replace("/login");
        }
      })
      .catch(() => {});
  }, [router]);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => fadeUp(cardRef.current, { y: 24, duration: 0.55 }));
    return () => ctx.revert();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.signup({
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
      });
      router.push("/login?registered=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setLoading(false);
    }
  };

  if (blocked) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        系统已关闭注册，正在跳转…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 via-white to-slate-100">
      <div ref={cardRef} className="w-full max-w-md">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">创建账户</CardTitle>
            <p className="mt-2 text-sm text-slate-500">注册后即可使用采集系统，数据与其他用户隔离</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">用户名</label>
                <Input
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  minLength={3}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">邮箱</label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">姓名（选填）</label>
                <Input
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">密码</label>
                <Input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  minLength={6}
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "注册中…" : "注册"}
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-slate-500">
              已有账户？{" "}
              <Link href="/login" className="text-primary-600 hover:underline">
                去登录
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
