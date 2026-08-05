import { supabase } from '@/lib/supabase';

async function getLatestCode() {
  const { data } = await supabase
    .from('daily_codes')
    .select('*')
    .order('code_date', { ascending: false })
    .limit(1)
    .single();
  return data;
}

async function getCodeHistory() {
  const { data } = await supabase
    .from('daily_codes')
    .select('*')
    .order('code_date', { ascending: false })
    .limit(14);
  return data || [];
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}

export default async function DailyCodePage() {
  const latest = await getLatestCode();
  const history = await getCodeHistory();

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">🔑 每日密码</h1>
        <p className="text-df-muted mt-2">多源交叉验证 · 每日 06:00 自动更新</p>
      </header>

      {/* 今日密码卡片 */}
      <section className="bg-gradient-to-br from-df-accent/10 to-df-accent/5 border border-df-accent/30 rounded-2xl p-8 text-center mb-8">
        {latest ? (
          <>
            <p className="text-df-muted text-sm mb-2">今日密码 · {formatDate(latest.code_date)}</p>
            <div className="flex items-center justify-center gap-4 mb-4">
              <code className="text-4xl sm:text-5xl font-bold font-mono text-df-accent tracking-widest">
                {latest.code_value}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(latest.code_value)}
                className="px-4 py-2 bg-df-accent text-df-bg rounded-lg font-medium hover:bg-df-accent/90 transition-colors"
              >
                📋 复制
              </button>
            </div>
            <div className="flex items-center justify-center gap-4 text-sm">
              <span className={`px-2 py-1 rounded ${latest.verified ? 'bg-df-green/20 text-df-green' : 'bg-df-yellow/20 text-df-yellow'}`}>
                {latest.verified ? '✅ 已验证' : '⚠️ 待验证'}
              </span>
              <span className="text-df-muted">来源: {latest.source_count} 个</span>
              <span className="text-df-muted">置信度: {(latest.confidence * 100).toFixed(0)}%</span>
            </div>
            {latest.sources && latest.sources.length > 0 && (
              <p className="text-xs text-df-muted mt-3">
                来源平台: {latest.sources.join(' · ')}
              </p>
            )}
          </>
        ) : (
          <>
            <p className="text-df-muted mb-4">今日密码尚未采集...</p>
            <p className="text-sm text-df-muted">系统将在 06:00 自动更新</p>
          </>
        )}
      </section>

      {/* 历史记录 */}
      <section className="bg-df-card border border-df-border rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">📜 近期密码记录</h2>
        {history.length === 0 ? (
          <p className="text-df-muted text-sm">暂无历史记录</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {history.map((c: any) => (
              <div key={c.id} className="bg-df-bg border border-df-border rounded-lg p-3 text-center">
                <p className="text-xs text-df-muted mb-1">{formatDate(c.code_date)}</p>
                <code className="text-sm font-mono font-bold text-df-accent">{c.code_value}</code>
                {!c.verified && <p className="text-xs text-df-yellow mt-1">待验证</p>}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 说明 */}
      <section className="mt-8 bg-df-card border border-df-border rounded-xl p-6">
        <h3 className="font-bold mb-2">ℹ️ 关于每日密码</h3>
        <ul className="text-sm text-df-muted space-y-1 list-disc list-inside">
          <li>系统每天 06:00 (北京时间) 自动从 B站/抖音/快手/百度 采集</li>
          <li>至少 2 个独立来源一致才会标记为「已验证」</li>
          <li>采集失败时会在 18:00 进行二次确认</li>
          <li>数据仅供参考，以游戏内实际为准</li>
        </ul>
      </section>
    </div>
  );
}
