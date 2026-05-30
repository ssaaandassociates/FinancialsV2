/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy /api/* to the FastAPI backend so the frontend can call it
  // without CORS. BACKEND_URL is set per-environment (Railway internal URL
  // in prod, http://localhost:8000 in dev).
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};
module.exports = nextConfig;
