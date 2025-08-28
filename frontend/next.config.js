/** @type {import('next').NextConfig} */
const nextConfig = {
  // 强制启用Fast Refresh
  reactStrictMode: true,
  
  // 开发环境优化
  experimental: {
    // 启用Turbopack（Next.js 13+的更快开发服务器）
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  
  // 启用文件监控优化
  webpack: (config, { dev }) => {
    if (dev) {
      // 增强文件监控
      config.watchOptions = {
        poll: 1000, // 每秒检查文件变化
        aggregateTimeout: 300, // 防抖延迟
        ignored: /node_modules/,
      }
    }
    return config
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig