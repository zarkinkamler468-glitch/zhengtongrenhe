import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  /** HTML 不长期缓存，避免部署后仍引用已删除的 chunk；带 hash 的静态资源可长期缓存 */
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
      {
        source: "/((?!_next/static).*)",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store, must-revalidate",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
