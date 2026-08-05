import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '三角洲情报站 | Delta Force Intel',
  description: '每日更新改枪码、跑刀路线、每日密码、干员分析',
  keywords: '三角洲行动,改枪码,跑刀路线,每日密码,干员分析,Delta Force',
  openGraph: {
    title: '三角洲情报站',
    description: '三角洲行动一站式情报平台',
    type: 'website'
  }
};

const navItems = [
  { href: '/', label: '首页' },
  { href: '/weapons', label: '改枪码' },
  { href: '/routes', label: '跑刀路线' },
  { href: '/daily-code', label: '每日密码' },
  { href: '/operators', label: '干员分析' }
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <nav className="sticky top-0 z-50 bg-df-bg/95 backdrop-blur border-b border-df-border">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="text-2xl">🎯</span>
              <span className="font-bold text-lg text-df-accent hidden sm:inline">三角洲情报站</span>
            </a>
            <div className="flex items-center gap-1 sm:gap-2">
              {navItems.map(item => (
                <a
                  key={item.href}
                  href={item.href}
                  className="px-3 py-2 rounded-lg text-sm hover:bg-df-card hover:text-df-accent transition-colors text-df-muted hover:text-white"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
        <footer className="border-t border-df-border mt-16 py-8 text-center text-df-muted text-sm">
          <p>© 2026 三角洲情报站 | 数据来源于公开平台，仅供学习交流</p>
          <p className="mt-2 text-xs">Powered by Next.js + Supabase + Cloudflare</p>
        </footer>
      </body>
    </html>
  );
}
