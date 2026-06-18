"use client";

import { useEffect } from "react";

const RELOAD_KEY = "chunk_reload_ts";
const RELOAD_COOLDOWN_MS = 30_000;

function isChunkLoadError(message: string | undefined): boolean {
  if (!message) return false;
  return (
    message.includes("ChunkLoadError") ||
    message.includes("Loading chunk") ||
    message.includes("Failed to fetch dynamically imported module")
  );
}

function isNextStaticAsset(url: string | undefined): boolean {
  if (!url) return false;
  try {
    const path = new URL(url, window.location.origin).pathname;
    return path.includes("/_next/static/");
  } catch {
    return url.includes("/_next/static/");
  }
}

/** 部署后 HTML 与 _next/static 版本不一致时，自动刷新一次拉取最新资源 */
export function ChunkErrorRecovery() {
  useEffect(() => {
    const tryReload = (reason: string) => {
      const last = Number(sessionStorage.getItem(RELOAD_KEY) || "0");
      if (Date.now() - last < RELOAD_COOLDOWN_MS) {
        console.warn("[chunk-recovery] 已刷新过，跳过:", reason);
        return;
      }
      sessionStorage.setItem(RELOAD_KEY, String(Date.now()));
      console.warn("[chunk-recovery] 检测到静态资源版本不一致，正在刷新页面…", reason);
      window.location.reload();
    };

    const onError = (event: ErrorEvent) => {
      const target = event.target;
      if (target instanceof HTMLScriptElement || target instanceof HTMLLinkElement) {
        const url = target instanceof HTMLScriptElement ? target.src : target.href;
        if (isNextStaticAsset(url)) {
          tryReload(`static asset failed: ${url}`);
          return;
        }
      }
      if (isChunkLoadError(event.message)) {
        tryReload(event.message);
      }
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      const msg =
        event.reason instanceof Error
          ? event.reason.message
          : typeof event.reason === "string"
            ? event.reason
            : "";
      if (isChunkLoadError(msg)) {
        event.preventDefault();
        tryReload(msg);
      }
    };

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);

  return null;
}
