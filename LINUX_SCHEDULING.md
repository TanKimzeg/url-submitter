# Linux 定时任务（systemd 与 cron）

本文提供在 Linux 上定时运行 `main.py` 的两种方式：systemd 定时器与 cron。

注意：以下示例假设你将项目部署到 `/opt/url-submitter`，请根据实际路径修改。

## 先决条件
- 已安装 Python 3.10+，并在部署机可运行 `python3`
- 项目目录包含 `main.py` 与 `sitemap.xml`
- 已获取并设置 API 密钥：`BING_API_KEY` 与 `INDEXNOW_API_KEY`

为项目准备环境
```bash
uv sync
```

---

## 方式一：systemd 定时器

1) 创建环境变量文件（建议集中管理）
```bash
sudo mkdir -p /etc/url-submitter /var/log/url-submitter
sudo tee /etc/url-submitter/env >/dev/null <<'EOF'
BING_API_KEY=your_bing_api_key
INDEXNOW_API_KEY=your_indexnow_api_key
# 使用 uv 运行，无需设置虚拟环境变量
EOF
```

2) 创建 systemd Service（/etc/systemd/system/url-submitter.service）
```ini
[Unit]
Description=Submit URLs to Bing & IndexNow
Wants=url-submitter.timer

[Service]
Type=oneshot
WorkingDirectory=/opt/url-submitter
EnvironmentFile=/etc/url-submitter/env
# 使用 uv 运行脚本
ExecStart=/bin/bash -lc "uv run python main.py --sitemap sitemap.xml --log /var/log/url-submitter/submit.log"

[Install]
WantedBy=multi-user.target
```

3) 创建 systemd Timer（/etc/systemd/system/url-submitter.timer）
- 每日 03:00 运行一次：
```ini
[Unit]
Description=Run URL Submitter daily at 03:00

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
Unit=url-submitter.service

[Install]
WantedBy=timers.target
```
- 或每 6 小时运行一次：
```ini
[Unit]
Description=Run URL Submitter every 6 hours

[Timer]
OnBootSec=5m
OnUnitActiveSec=6h
Persistent=true
Unit=url-submitter.service

[Install]
WantedBy=timers.target
```

4) 重新加载并启用
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now url-submitter.timer
# 手动测试一次：
sudo systemctl start url-submitter.service
# 查看状态与日志：
systemctl status url-submitter.service
journalctl -u url-submitter.service -n 50 --no-pager
```

---

## 方式二：cron

1) 创建运行脚本 `/opt/url-submitter/run-url-submitter.sh`
```bash
sudo tee /opt/url-submitter/run-url-submitter.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8

# 集中管理环境变量（推荐）：/etc/url-submitter/env
if [ -f /etc/url-submitter/env ]; then
  set -a
  . /etc/url-submitter/env
  set +a
else
  echo "Missing /etc/url-submitter/env" >&2
  exit 1
fi

# 确保日志目录存在
mkdir -p /var/log/url-submitter

# 切到项目目录
cd /opt/url-submitter

# 使用 uv 运行（程序内部日志写到 submit.log；cron 自身输出请在 crontab 行里重定向）
uv run python main.py --sitemap sitemap.xml --log /var/log/url-submitter/submit.log
EOF

sudo chmod +x /opt/url-submitter/run-url-submitter.sh
```

2) 添加 crontab 任务
- 每10天运行一次：
```bash
( crontab -l 2>/dev/null; echo "0 0 1,11,21 * * /opt/url-submitter/run-url-submitter.sh >> /var/log/url-submitter/cron.log 2>&1" ) | crontab -
```

---

## 关于 /etc/url-submitter/env 配置

这个文件用于集中保存敏感环境变量，供 systemd Service 的 `EnvironmentFile=` 与 cron 脚本加载。

- 位置：`/etc/url-submitter/env`
- 被谁加载：
  - systemd：`EnvironmentFile=/etc/url-submitter/env`
  - cron 脚本：`set -a; . /etc/url-submitter/env; set +a`

推荐格式（每行一个 `KEY=VALUE`，不写 `export`，尽量不要加引号）：
```env
# 必应 URL 提交 API
BING_API_KEY=your_bing_api_key

# IndexNow 提交 API
INDEXNOW_API_KEY=your_indexnow_api_key
```

创建与权限（避免泄露）：
```bash
sudo mkdir -p /etc/url-submitter
sudo touch /etc/url-submitter/env

# 编辑
sudo vim /etc/url-submitter/env
```

---

## 常见问题
- 权限问题：确保脚本可执行（`chmod +x`）且日志目录可写
- 虚拟环境：已统一为 `uv run`，无需手动激活 venv
- 环境变量：推荐使用 `/etc/url-submitter/env` 管理，避免写死在脚本或单元文件中
