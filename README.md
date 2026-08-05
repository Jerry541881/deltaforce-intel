# 🎯 三角洲情报站

> 三角洲行动 零成本自动化情报站 —— 改枪码 / 跑刀路线 / 每日密码 / 干员分析

## ✅ 配置状态

| 服务 | 状态 |
|------|------|
| Supabase 数据库（8张表） | ✅ 已建好 |
| Supabase URL | ✅ 已配置 |
| 智谱AI Key | ✅ 已配置 |
| Cloudflare Account | ✅ 已配置 |
| GitHub Secrets | 🔄 待添加（见下方） |

## 🚀 快速启动（3步上线）

### 第①步：添加 GitHub Secrets

打开：https://github.com/Jerry541881/deltaforce-intel/settings/secrets/actions

点 **New repository secret**，添加以下 6 个：

| Secret 名称 | 值 |
|---|---|
| `SUPABASE_URL` | `https://oiwrcxuhanvpyxehgimr.supabase.co` |
| `SUPABASE_ANON_KEY` | `xxx` |
| `SUPABASE_SERVICE_ROLE_KEY` | `xxx` |
| `ZHIPU_API_KEY` | `xxx` |
| `CLOUDFLARE_API_TOKEN` | `xxx` |
| `CLOUDFLARE_ACCOUNT_ID` | `xxx` |

### 第②步：推送代码到 GitHub

在你电脑上（需安装 Git + Node.js 20+）：

```bash
# 进入项目目录
cd deltaforce-intel

# 安装依赖
npm install

# 本地预览（浏览器打开 http://localhost:3000）
npm run dev
# 确认首页正常显示后，按 Ctrl+C 停止

# 初始化 Git 并推送到 GitHub
git init
git add .
git commit -m "feat: 三角洲情报站上线"
git remote add origin https://github.com/Jerry541881/deltaforce-intel.git
git push -u origin main
```

### 第③步：Cloudflare Pages 连接

1. 登录 https://dash.cloudflare.com
2. 左侧 **Pages** → **Create a project**
3. 选 **Connect to Git** → 授权 GitHub → 选 `deltaforce-intel`
4. Framework preset 选 **Next.js**
5. 构建命令：`npm run build`
6. 环境变量（Environment variables）添加：
   - `NEXT_PUBLIC_SUPABASE_URL` = `https://oiwrcxuhanvpyxehgimr.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `xxx`
7. 点 **Deploy** → 等 2-3 分钟 → 拿到 `xxx.pages.dev` 地址

## 📁 项目结构

```
deltaforce-intel/
├── .github/workflows/     # 自动化调度（每天自动采集+部署）
├── src/app/               # 前端页面（Next.js App Router）
├── lib/                   # 数据库客户端 + AI提取
├── scripts/               # Python 采集脚本
├── supabase/schema.sql     # 数据库建表SQL
└── SETUP_SECRETS.md       # 详细配置指南
```

## 🔄 自动化流程

| 任务 | 频率 | 说明 |
|------|------|------|
| 采集改枪码+路线 | 每天 06:00 | B站+抖音+快手→AI提取→入库 |
| 采集每日密码 | 每天 4 次 | 多源交叉验证 |
| 更新干员分析 | 每 3 月 | 全量刷新 |

## 💰 成本

**0 元/月** —— 全部使用免费额度

## 📝 注意事项

- `.env.local` 已在 `.gitignore` 中，不会被推送到 GitHub
- Service Role Key 权限极高，只在 Secrets 中配置
- 抖音/快手反爬较强，初期采集量可能有限，后续可加 Playwright 增强
- 智谱免费额度用完后，代码已内置 DeepSeek 兜底逻辑
