# 论文开题写作助手 Skill

[English](README.md)

这是一个适配 Jenius 的论文开题写作 Skill：先通过普通 Assistant 对话补齐四项关键信息，再使用维普 API 检索真实文献，最后把结构化开题信息和文献证据交给宿主 Assistant 撰写正文。

> 本项目是独立社区项目，与维普不存在官方隶属或背书关系。

## 核心能力

- 一次性确认学位层级、专业背景、研究子方向和交付格式；
- 从可见对话历史复用答案，避免重复询问；
- 信息完整后才调用维普主题词检索和 AI 检索；
- 按 DOI、文献 ID、规范化标题去重；
- 不补造作者、题名、期刊、年份或 DOI；
- 维普不可用时仍可撰写非引文章节，但明确标记参考文献不可用；
- 运行时只依赖 Python 标准库。

## 重要职责边界

```text
runner.py / main.py
  ├─ 补齐开题信息
  └─ 整理文献证据
           ↓ ready_to_write
宿主 Assistant
  ├─ 撰写完整开题报告
  └─ 按沙箱能力生成 Markdown / Word / LaTeX / PDF
```

`runner.py` 没有 `write_proposal` 动作，这是设计边界，不是缺失依赖。

## 快速体验

```bash
python runner.py --input examples/first-turn-request.json --pretty
```

完整信息测试：

```bash
python runner.py --input examples/complete-request.json --pretty
```

未配置维普 Key 时仍会返回 `ready_to_write`，但 `literature_evidence.status` 为 `unavailable`，不会生成虚假论文。

## 配置维普 API

Linux/macOS：

```bash
export CQVIP_API_KEY="你的Key"
```

PowerShell：

```powershell
$env:CQVIP_API_KEY = "你的Key"
```

Key 只能保存在运行环境中，不得写入源代码、请求 JSON、日志、示例、ZIP、Issue 或 Pull Request。沙箱还必须允许访问：

```text
superapi.cqvip.com:443
```

## 安装到 Jenius

1. 下载 GitHub Release 中的 ZIP，或自行打包；
2. 将 ZIP 放到 Jenius 与沙箱都能访问的 URL；
3. 通过 Jenius 自定义 Skill 接口注册该 URL；
4. 在 Agent 配置中选择 `thesis-proposal-writer`；
5. 在实际沙箱服务中配置 `CQVIP_API_KEY`；
6. 开放维普域名的 HTTPS 出站访问。

## 开发与验证

离线测试：

```bash
python -m unittest discover -s tests -v
```

真实接口测试仅在显式开启时运行：

```bash
CQVIP_LIVE_TEST=1 CQVIP_API_KEY="你的Key" \
  python -m unittest tests.test_live_api -v
```

跨平台打包：

```bash
python scripts/package_skill.py --output-dir dist
```

打包器会检查硬编码 Key、必需文件和 ZIP 路径格式，并生成 SHA-256 文件。

更多内容见：[架构说明](docs/architecture.md)、[故障排查](docs/troubleshooting.md)、[隐私与学术诚信](docs/privacy-and-academic-integrity.md)。

首次发布时还应配置[推荐的 GitHub 仓库设置](docs/repository-settings.md)。

## 限制

- 维普返回的题录和摘要不等于已阅读论文全文；
- 实时检索受沙箱网络、接口权限、调用额度和服务状态影响；
- 生成内容必须由用户审核并遵守所在学校的学术规范；
- Word/PDF 生成取决于宿主沙箱是否提供文档工具。

## 许可证

项目代码使用 [MIT License](LICENSE)。维普接口和文献元数据仍受维普服务条款及用户账号权限约束。
