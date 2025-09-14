# URL 提交器 (RSS → Bing / IndexNow)

从 RSS 格式的站点地图中提取文章链接，自动提交到 Bing URL Submission API 与 IndexNow。

## 功能
- 解析 RSS 站点地图中的 `<item><link>`，提取 URL
- 提交到 Bing URL Submission API（需 BING_API_KEY）
- 提交到 IndexNow（需 INDEXNOW_API_KEY，并在站点根目录放置验证文件）
- 控制台彩色日志，支持写入日志文件（--log）

## 运行环境与依赖
安装依赖（任选一种方式）：
```shell
uv sync
```

## 使用方法

查看基本用法:
```bash
python main.py -h
```

### 必应API提交

首先需要获取必应网站管理员工具的[API密钥](https://blogs.bing.com/webmaster/may-2019/Easy-set-up-guide-for-Bing%E2%80%99s-Adaptive-URL-submission-API), 然后设置环境变量:

```bash
# Windows PowerShell
$env:BING_API_KEY="your_bing_api_key"
$env:INDEXNOW_API_KEY="your_indexNow_api_key"
python main.py

# Windows CMD
set BING_API_KEY=your_bing_api_key
set INDEXNOW_API_KEY="your_indexNow_api_key"
python main.py

# Linux/Mac
export BING_API_KEY="your_bing_api_key"
export INDEXNOW_API_KEY="your_indexNow_api_key"
python main.py
```

## 注意事项

- 确认 `sitemap.xml` 文件的位置
- RSS格式的站点地图必须包含有效的 `<item>` 和 `<link>` 标签
- 必应API提交有[频率限制](https://www.bing.com/webmasters/help/url-submission-62f2860b), 建议适量提交

## 故障排除

### 常见问题

1. **XML解析错误**: 检查sitemap.xml文件格式是否正确
2. **找不到URL**: 确认RSS文件中包含 `<item><link>` 结构
3. **API提交失败**: 检查API密钥是否有效，网站是否已验证

### 调试模式

如果遇到问题，可以查看程序输出的日志来定位问题。
