import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,

  // Next.js Image Optimization for external CDN images (Instagram, TikTok, YouTube)
  images: {
    remotePatterns: [
      // Instagram CDN variants
      { protocol: 'https', hostname: '**.cdninstagram.com' },
      { protocol: 'https', hostname: '**.fbcdn.net' },
      { protocol: 'https', hostname: 'instagram.*.fna.fbcdn.net' },
      { protocol: 'https', hostname: 'scontent*.cdninstagram.com' },
      // TikTok CDN
      { protocol: 'https', hostname: '**.tiktokcdn.com' },
      { protocol: 'https', hostname: '**.tiktokcdn-us.com' },
      // YouTube
      { protocol: 'https', hostname: 'i.ytimg.com' },
      { protocol: 'https', hostname: 'img.youtube.com' },
      // Fallback proxy (weserv.nl)
      { protocol: 'https', hostname: 'images.weserv.nl' },
    ],
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin();
export default withNextIntl(nextConfig);
