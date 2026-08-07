=====================================================
  智谱AI版每日密码爬虫 - YAML工作流包
=====================================================

文件清单:
  daily-code.yml ← 每日密码工作流（覆盖到 .github/workflow/）

工作机制:
  1. 每天自动运行2次（北京时间 12:00 和 18:00）
  2. 调用智谱AI Web Search API 联网搜索
  3. 提取6张地图密码 → 写入 Supabase daily_codes 表

需要配置的 GitHub Secrets:
  ZHIPU_API_KEY            ← 智谱AI开放平台获取
  SUPABASE_URL               ← 你的Supabase项目URL
  SUPABASE_SERVICE_ROLE_KEY  ← Supabase service_role key

获取 ZHIPU_API_KEY:
  1. 打开 https://open.bigmodel.cn/
  2. 注册/登录 → 控制台 → API Keys
  3. 创建API Key → 复制
  4. 粘贴到 GitHub Settings → Secrets → New

工作流触发方式:
  - 定时自动: cron 0 12,18 * * * (UTC时间)
  - 手动触发: Actions页面 → Run workflow

=====================================================
