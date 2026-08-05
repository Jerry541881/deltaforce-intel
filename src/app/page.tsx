import Link from 'next/link';

const modules = [
  {
    href: '/weapons',
    icon: '🔫',
    title: '改枪码库',
    desc: '按枪种→强度分级，每日自动搜集全网最新改枪码，一键复制即用',
    tag: '每日更新',
    tagColor: 'bg-df-green/20 text-df-green'
  },
  {
    href: '/routes',
    icon: '🗺️',
    title: '跑刀路线',
    desc: '各地图出生点位+推荐跑刀路线，图文并茂，助你高效摸金',
    tag: '每日更新',
    tagColor: 'bg-df-blue/20 text-df-blue'
  },
  {
    href: '/daily-code',
    icon: '🔑',
    title: '每日密码',
    desc: '每日最新密码汇总，多源交叉验证，到点自动更新',
    tag: '每日 06:00',
    tagColor: 'bg-df-accent/20 text-df-accent'
  },
  {
    href: '/operators',
    icon: '👤',
    title: '干员分析',
    desc: '全干员优劣势详解，版本更新后定期刷新，选人不再纠结',
    tag: '每季更新',
    tagColor: 'bg-df-purple/20 text-df-purple'
  }
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-4">
          <span className="text-df-accent">三角洲</span>情报站
        </h1>
        <p className="text-df-muted text-lg max-w-2xl mx-auto">
          一站式三角洲行动情报平台 — 改枪码、跑刀路线、每日密码、干员分析
        </p>
        <div className="mt-6 flex items-center justify-center gap-4 text-sm text-df-muted">
          <span className="flex items-center gap-1">🟢 系统运行中</span>
          <span>最后更新: {new Date().toLocaleDateString('zh-CN')}</span>
        </div>
      </section>

      {/* 四大模块卡片 */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        {modules.map(m => (
          <Link
            key={m.href}
            href={m.href}
            className="group bg-df-card border border-df-border rounded-xl p-6 hover:border-df-accent/50 transition-all hover:shadow-lg hover:shadow-df-accent/5"
          >
            <div className="flex items-start justify-between">
              <div className="text-4xl mb-3">{m.icon}</div>
              <span className={`text-xs px-2 py-1 rounded-full ${m.tagColor}`}>{m.tag}</span>
            </div>
            <h3 className="text-xl font-bold mb-2 group-hover:text-df-accent transition-colors">{m.title}</h3>
            <p className="text-df-muted text-sm leading-relaxed">{m.desc}</p>
            <div className="mt-4 text-df-accent text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              进入 →
            </div>
          </Link>
        ))}
      </section>

      {/* 数据来源说明 */}
      <section className="mt-12 bg-df-card border border-df-border rounded-xl p-6">
        <h3 className="font-bold text-lg mb-3">📡 数据来源</h3>
        <p className="text-df-muted text-sm">
          系统每日自动采集 B站、抖音、快手、虎牙 等平台的三角洲行动相关内容，
          经 AI 结构化提取后入库展示。所有数据均来自公开渠道，仅供学习交流使用。
        </p>
      </section>
    </div>
  );
}
