/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // 告诉 Next.js 要生成静态网站
  basePath: '/deltaforce-intel', // 👈 重点！这就是我们的“地图”，告诉它包裹在哪个子文件夹里
  assetPrefix: '/deltaforce-intel/', // 👈 重点！配合上面的设置，确保图片和样式表也能正确加载
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig