/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors (only for _old.tsx files)
    ignoreBuildErrors: false,
  },
  // Performance optimizations
  swcMinify: true,
  reactStrictMode: true,
  // Enable compression
  compress: true,
  // Optimize images
  images: {
    unoptimized: true, // Disable image optimization for faster builds
  },
  // Reduce JavaScript bundle size
  modularizeImports: {
    '@/components/ui': {
      transform: '@/components/ui/{{member}}',
    },
  },
};

export default nextConfig;
