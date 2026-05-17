# Heartopia Discord 服务器数据追踪

追踪 Heartopia Discord 服务器的注册成员数与在线人数，通过 ECharts 可视化展示历史趋势。

**页面地址:** https://as167888.github.io/heartopia-tracker/

## 架构

```
Discord API (每小时)
     │
     ▼
Cloudflare Worker ──► GitHub API ──► data/heartopia_data.json
                                        │
                                        ▼
                                   GitHub Pages ──► index.html (ECharts 可视化)
```

- **数据采集:** Cloudflare Worker (`worker/src/index.js`) 每小时的第 7 分通过 Discord Invite API 抓取成员数和在线人数，写入 `data/heartopia_data.json`
- **数据存储:** GitHub 仓库 `data/heartopia_data.json`，每条记录包含北京时间戳、`member_count`、`presence_count`
- **可视化:** GitHub Pages 托管 `index.html`，使用 ECharts 5.5 渲染双图趋势

## 项目结构

```
├── index.html              # 前端仪表盘 (ECharts)
├── data/
│   └── heartopia_data.json # 历史数据
├── worker/
│   ├── wrangler.toml        # Cloudflare Worker 配置
│   ├── package.json
│   └── src/
│       └── index.js         # Worker 采集脚本
└── .gitignore
```

## Worker 部署

```bash
cd worker
npm install
npx wrangler secret put GITHUB_TOKEN   # 设置 GitHub PAT (需 repo 写入权限)
npx wrangler deploy
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `DISCORD_API` | Discord Invite API 地址 |
| `GITHUB_OWNER` | GitHub 用户名 |
| `GITHUB_REPO` | 仓库名 |
| `DATA_PATH` | JSON 数据在仓库中的路径 |
| `GITHUB_TOKEN` | GitHub 个人访问令牌 (Secret) |
