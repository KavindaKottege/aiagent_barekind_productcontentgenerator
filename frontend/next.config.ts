import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',  // Allow larger Excel files
    },
  },
};

export default nextConfig;
