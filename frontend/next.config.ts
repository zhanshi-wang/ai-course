import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  rewrites: async () => [
    {
      source: "/xapi/:path*",
      destination: "http://backend:8000/:path*",
    },
  ],
};

export default nextConfig;
