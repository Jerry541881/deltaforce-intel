import { supabase } from '@/lib/supabase';

const difficultyColors: Record<string, string> = {
  easy: 'bg-df-green/20 text-df-green',
  medium: 'bg-df-blue/20 text-df-blue',
  hard: 'bg-df-red/20 text-df-red'
};

const riskColors: Record<string, string> = {
  low: 'text-df-green',
  medium: 'text-df-blue',
  high: 'text-df-red'
};

const mapIcons: Record<string, string> = {
  '零号大坝': '🌊', '航天基地': '🚀', '巴克什': '🏙️', '终极战场': '⚔️'
};

async function getRoutes() {
  const { data: maps } = await supabase
    .from('maps').select('*').order('id');
  const { data: routes } = await supabase
    .from('route_guides')
    .select('*, maps(name)')
    .eq('status', 'published')
    .order('difficulty');
  return { maps: maps || [], routes: routes || [] };
}

export default async function RoutesPage() {
  const { maps, routes } = await getRoutes();

  // 按地图分组
  const grouped: Record<string, any[]> = {};
  for (const r of routes) {
    const mapName = r.maps?.name || '其他';
    if (!grouped[mapName]) grouped[mapName] = [];
    grouped[mapName].push(r);
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">🗺️ 跑刀路线</h1>
        <p className="text-df-muted mt-2">各地图出生点位 + 推荐路线 · 每日自动更新</p>
        <div className="mt-3 flex items-center gap-3 text-xs">
          <span className="px-2 py-1 rounded bg-df-green/20 text-df-green">简单 = 新手友好</span>
          <span className="px-2 py-1 rounded bg-df-blue/20 text-df-blue">中等 = 需一定装备</span>
          <span className="px-2 py-1 rounded bg-df-red/20 text-df-red">困难 = 高风险高回报</span>
        </div>
      </header>

      {Object.keys(grouped).length === 0 ? (
        <div className="bg-df-card border border-df-border rounded-xl p-12 text-center">
          <p className="text-df-muted">暂无路线数据，等待采集任务填充...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {maps.map(map => {
            const items = grouped[map.name] || [];
            if (items.length === 0) return null;
            return (
              <section key={map.id} className="bg-df-card border border-df-border rounded-xl p-6">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="text-2xl">{mapIcons[map.name] || '🗺️'}</span>
                  {map.name}
                  <span className="text-sm font-normal text-df-muted">({items.length} 条路线)</span>
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {items.map((r, idx) => (
                    <div key={idx} className="bg-df-bg border border-df-border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{r.title}</h3>
                        <div className="flex gap-1">
                          <span className={`text-xs px-2 py-0.5 rounded ${difficultyColors[r.difficulty] || difficultyColors['medium']}`}>
                            {r.difficulty === 'easy' ? '简单' : r.difficulty === 'hard' ? '困难' : '中等'}
                          </span>
                        </div>
                      </div>
                      {r.expected_loot && (
                        <p className="text-sm text-df-accent mb-2">💰 {r.expected_loot}</p>
                      )}
                      {r.risk_level && (
                        <p className={`text-xs mb-2 ${riskColors[r.risk_level] || 'text-df-muted'}`}>
                          ⚠️ 风险: {r.risk_level === 'low' ? '低' : r.risk_level === 'high' ? '高' : '中'}
                        </p>
                      )}
                      {r.steps && r.steps.length > 0 && (
                        <ol className="text-sm text-df-muted space-y-1 mt-2 list-decimal list-inside">
                          {r.steps.slice(0, 5).map((s: any, i: number) => (
                            <li key={i}>{s.action || s}</li>
                          ))}
                        </ol>
                      )}
                      {r.video_url && (
                        <a href={r.video_url} target="_blank" rel="noopener noreferrer"
                           className="inline-block mt-3 text-xs text-df-blue hover:underline">
                          📺 观看视频攻略 →
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
          📅 最后更新: {new Date().toLocaleDateString('zh-CN')} | 数据由 AI 自动提取
        </p>
      </div>
    </div>
  );
}
