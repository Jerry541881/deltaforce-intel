# GitHub Secrets 配置指南

打开链接（替换用户名）：
`https://github.com/Jerry541881/deltaforce-intel/settings/secrets/actions`

点 **New repository secret**，逐个添加以下 6 个：

| Secret 名称 | 值 |
|---|---|
| `SUPABASE_URL` | `https://oiwrcxuhanvpyxehgimr.supabase.co` |
| `SUPABASE_ANON_KEY` | `xxx` |
| `SUPABASE_SERVICE_ROLE_KEY` | `xxx` |
| `ZHIPU_API_KEY` | `xxx` |
| `CLOUDFLARE_API_TOKEN` | `xxx` |
| `CLOUDFLARE_ACCOUNT_ID` | `xxx` |

---

## ⚡ 快速操作

所有值已确认，直接复制粘贴即可，无需再查找。

添加完 6 个 Secrets 后，页面应显示：
```
✅ SUPABASE_URL
✅ SUPABASE_ANON_KEY
✅ SUPABASE_SERVICE_ROLE_KEY
✅ ZHIPU_API_KEY
✅ CLOUDFLARE_API_TOKEN
✅ CLOUDFLARE_ACCOUNT_ID
```

---

## 然后做什么？

Secrets 配完后，在你电脑上：

```bash
# 进入项目目录
cd deltaforce-intel

# 安装依赖
npm install

# 本地预览（浏览器打开 http://localhost:3000）
npm run dev

# 确认首页能显示后，Ctrl+C 停止

# 初始化 Git 并推送到 GitHub
git init
git add .
git commit -m "feat: 三角洲情报站完整项目"
git remote add origin https://github.com/Jerry541881/deltaforce-intel.git
git push -u origin main
```

推送后：
1. GitHub Actions 自动运行 → 部署到 Cloudflare Pages
2. 去 Cloudflare Pages 看构建状态 → 拿到 `xxx.pages.dev` 地址
3. 网站上线！
