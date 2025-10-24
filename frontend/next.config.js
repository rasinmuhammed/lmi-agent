/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Optimize images
  images: {
    remotePatterns: [], // Updated from 'domains'
    formats: ['image/webp', 'image/avif'],
  },

  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Add any custom webpack config here
    return config;
  },

  // Redirects
  async redirects() {
    return [];
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },

  // Fix for multiple lockfiles warning
  outputFileTracingRoot: __dirname,
};

module.exports = nextConfig;