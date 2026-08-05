import Link from 'next/link';
import { supabase } from '@/lib/supabase';

const tierColors: Record<string, string> = {
  T0: 'bg-df-accent/20 text-df-accent border-df-accent/30',
  T1: 'bg-df-blue/20 text-df-blue border-df-blue/30',
  T2: 'bg-df-muted/20 text-df-muted border-df-muted/30'
};

const categoryIcons: Record<string, string> = {
  '突击步枪': '🔫', '冲锋枪': '🪖', '狙击枪': '🎯',
  '战斗步枪': '⚔️', '轻机枪': '⚙️', '霰弹枪': '💥', '手枪': '🔖'
};

// 服务端组件，直接读 Supabase
async function getWeaponData() {
  const { data: categories } = await supabase
    .from('weapon_categories').select('*').order('display_order');
  const { data: tiers } = await supabase
    .from('tier_levels').select('*').order('display_order');
  const { data: builds } = await supabase
    .from('weapon_builds')
    .select('*, weapon_categories(name), tier_levels(name)')
    .eq('status', 'published')
    .order('confidence_score', { ascending: false });

  return { categories: categories || [], tiers: tiers || [], builds: builds || [] };
}

export default async function WeaponsPage() {
  const { categories, builds } = await getWeaponData();

  // 按分类分组
  const grouped: Record<string, any[]> = {};
  for (const b of builds) {
    const catName = b.weapon_categories?.name || '其他';
    if (!grouped[catName]) grouped[catName] = [];
    grouped[catName].push(b);
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">🔫 改枪码库</h1>
        <p className="text-df-muted mt-2">按枪种分类 · 按强度分级 · 每日自动更新</p>
        <div className="mt-3 flex items-center gap-3 text-xs">
          <span className="px-2 py-1 rounded bg-df-accent/20 text-df-accent">T0 = 版本最强</span>
          <span className="px-2 py-1 rounded bg-df-blue/20 text-df-blue">T1 = 可用性强</span>
          <span className="px-2 py-1 rounded bg-df-muted/20 text-df-muted">T2 = 特定场景</span>
        </div>
      </header>

      {Object.keys(grouped).length === 0 ? (
        <div className="bg-df-card border border-df-border rounded-xl p-12 text-center">
          <p className="text-df-muted">暂无数据，等待每日采集任务填充...</p>
          <p className="text-df-muted text-sm mt-2">也可以手动插入示例数据体验功能</p>
        </div>
      ) : (
        <div className="space-y-8">
          {categories.map(cat => {
            const weapons = grouped[cat.name] || [];
            if (weapons.length === 0) return null;
            return (
              <section key={cat.id} className="bg-df-card border border-df-border rounded-xl p-6">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="text-2xl">{categoryIcons[cat.name] || '🔫'}</span>
                  {cat.name}
                  <span className="text-sm font-normal text-df-muted">({weapons.length} 条)</span>
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {weapons.map((w, idx) => (
                    <div key={idx} className="bg-df-bg border border-df-border rounded-lg p-4 hover:border-df-accent/30 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{w.weapon_name}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded border ${tierColors[w.tier_levels?.name] || tierColors['T1']}`}>
                          {w.tier_levels?.name || 'T1'}
                        </span>
                      </div>
                      {w.title && <p className="text-sm text-df-accent mb-1">{w.title}</p>}
                      {w.description && <p className="text-sm text-df-muted mb-3">{w.description}</p>}
                      {w.tags && w.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {w.tags.map((tag: string, i: number) => (
                            <span key={i} className="text-xs px-2 py-0.5 bg-df-border/30 rounded">{tag}</span>
                          ))}
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <code className="flex-1 bg-df-bg border border-df-border rounded px-3 py-2 text-xs font-mono text-df-accent truncate">
                          {w.build_code}
                        </code>
                        <button
                          onClick={() => navigator.clipboard.writeText(w.build_code)}
                          className="shrink-0 px-3 py-2 bg-df-accent text-df-bg rounded font-medium text-sm hover:bg-df-accent/90 transition-colors"
                        >
                          复制
                        </button>
                      </div>
                      {w.source_url && (
                        <a href={w.source_url} target="_blank" rel="noopener noreferrer"
                           className="inline-block mt-2 text-xs text-df-blue hover:underline">
                          查看来源 →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      <div className="mt-8 bg-df-card border border-df-border rounded-xl p-6 text-center">
        <p className="text-df-muted text-sm">
          📅 最后更新: {new Date().toLocaleDateString('zh-CN')} | 下次更新: 每日 06:00
        </p>
        <p className="text-df-muted text-xs mt-2">
          数据来源: B站 / 抖音 / 快手 / 虎牙 | 由 AI 自动提取
        </p>
      </div>
    </div>
  );
}
