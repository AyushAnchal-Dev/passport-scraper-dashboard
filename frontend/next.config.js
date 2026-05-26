/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Allow external image domains (DiceBear avatars)
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'api.dicebear.com',
        pathname: '/**',
      },
    ],
    unoptimized: true,  // Required for Docker / static export
  },

  // Disable server-side fetching timeouts for long NLP pipeline waits
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },

  // Disable x-powered-by header for security
  poweredByHeader: false,

  // Strict mode for catching bugs
  reactStrictMode: true,
}

module.exports = nextConfig
