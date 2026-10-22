import type { NextConfig } from "next";
import { API_PROXY_PATH, API_URL, UPLOAD_API_URL } from "./src/lib/apiUrl";

const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = isDev
  ? {
      rewrites: async () => [
        // Upload service: file uploads and the local stand-in for S3 presigned PUT URLs
        { source: `${API_PROXY_PATH}/upload`, destination: `${UPLOAD_API_URL}/upload` },
        { source: `${API_PROXY_PATH}/local-upload/:path*`, destination: `${UPLOAD_API_URL}/local-upload/:path*` },
        { source: `${API_PROXY_PATH}/:path*`, destination: `${API_URL}/:path*` },
      ],
      experimental: {
        // Report generation answers after 1-3 minutes; the proxy default is 30 s
        proxyTimeout: 600_000,
      },
    }
  : {
      output: 'export',
      trailingSlash: true,
      images: { unoptimized: true },
    };

export default nextConfig;
