import { supabase } from '@/lib/supabase';

const roleColors: Record<string, string> = {
  '突击': 'bg-df-red/20 text-df-red',
  '支援': 'bg-df-green/20 text-df-green',
  '侦察': 'bg-df-blue/20 text-df-blue',
  '工程': 'bg-df-purple/20 text-df-purple',
};

function getRoleColor(role: string): string {
  for (const key of Object.keys(roleColors)) {
    if (role?.includes(key)) return roleColors[key];
  }
  return 'bg-df-muted/20 text-df-muted';
}

function getRatingColor(rating: number): string {
  if (rating >= 8) return 'text-df-green';
  if (rating >= 6) return 'text-df-accent';
  return 'text-df-muted';
}

async function getOperators() {
  const { data } = await supabase
    .from('operator_analysis')
    .select('*')
    .eq('status', 'published')
    .order('overall_rating', { ascending: false });
  return data || [];
}

export default async function OperatorsPage() {
  const operators = await getOperators();

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">👤 干员分析</h1>
        <p className="text-df-muted mt-2">全干员优劣势详解 · 每3个月自动更新</p>
        <div className="mt-3 flex items-center gap-3 text-xs">
          <span className="px-2 py-1 rounded bg-df-green/20 text-df-green">★ 8+ 强势推荐</span>
          <span className="px-2 py-1 rounded bg-df-accent/20 text-df-accent">★ 6-8 可用</span>
          <span className="px-2 py-1 rounded bg-df-muted/20 text-df-muted">★ &lt;6 特定场景</span>
        </div>
      </header>

      {operators.length === 0 ? (
        <div className="bg-df-card border border-df-border rounded-xl p-12 text-center">
          <p className="text-df-muted">暂无干员数据，等待季度更新...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {operators.map((op: any) => (
            <div key={op.id} className="bg-df-card border border-df-border rounded-xl p-6 hover:border-df-accent/30 transition-colors">
              {/* 头部 */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold">{op.operator_name}</h3>
                  {op.role && (
                    <span className={`text-xs px-2 py-0.5 rounded mt-1 inline-block ${getRoleColor(op.role)}`}>
                      {op.role}
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${getRatingColor(op.overall_rating || 0)}`}>
                    {(op.overall_rating || 0).toFixed(1)}
                  </div>
                  <div className="text-xs text-df-muted">/ 10</div>
                </div>
              </div>

              {/* 优势 */}
              {op.strengths && op.strengths.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-df-green mb-1">✅ 优势</p>
                  <div className="flex flex-wrap gap-1">
                    {op.strengths.map((s: string, i: number) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-df-green/10 text-df-green rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 劣势 */}
              {op.weaknesses && op.weaknesses.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-df-red mb-1">❌ 劣势</p>
                  <div className="flex flex-wrap gap-1">
                    {op.weaknesses.map((w: string, i: number) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-df-red/10 text-df-red rounded">
                        {w}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 适合地图 */}
              {op.best_maps && op.best_maps.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-df-blue mb-1">🗺️ 适合地图</p>
                  <div className="flex flex-wrap gap-1">
                    {op.best_maps.map((m: string, i: number) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-df-blue/10 text-df-blue rounded">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 推荐武器 */}
              {op.best_weapons && op.best_weapons.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-df-accent mb-1">🔫 推荐武器</p>
                  <div className="flex flex-wrap gap-1">
                    {op.best_weapons.map((w: string, i: number) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-df-accent/10 text-df-accent rounded">
                        {w}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 打法风格 */}
              {op.playstyle && (
                <p className="text-sm text-df-muted mt-3 italic">"{op.playstyle}"</p>
              )}

              {/* 版本 */}
              {op.version && (
                <p className="text-xs text-df-muted mt-2">版本: {op.version}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 bg-df-card border border-df-border rounded-xl p-6 text-center">
        <p className="text-df-muted text-sm">
          📅 下次更新: 每3个月第一天的 10:00 | 当前版本: S10
        </p>
        <p className="text-df-muted text-xs mt-2">
          数据由 AI 汇总 B站/抖音/快手/虎牙 攻略内容生成
        </p>
      </div>
    </div>
  );
}
