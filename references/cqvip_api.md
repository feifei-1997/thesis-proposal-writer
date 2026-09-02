# CQVIP API 接入参考

官方文档入口：<https://super.cqvip.com/api-docs/>

## 认证与基础地址

```http
Authorization: Bearer API_KEY
Content-Type: application/json
```

默认基础地址：`https://superapi.cqvip.com`。

Key 必须通过 `CQVIP_API_KEY` 注入。`CQVIP_BASE_URL` 仅用于部署方覆盖基础地址，客户端要求其为 HTTPS。

## 本 Skill 使用的接口

| 动作 | 方法与路径 | 请求字段 |
|---|---|---|
| 简单检索 | `POST /unifiedsearch/search/v1/paper/simple-search` | `page`、`size`、`content` |
| AI 检索 | `POST /unifiedsearch/search/v1/paper/ai-search` | `size`、`content` |
| 文献详情 | `POST /unifiedsearch/search/v1/paper-detail` | `id` |
| 引用格式 | `POST /unifiedsearch/search/v1/bibliography-citation` | `paperDetails`、`formatType` |

简单检索文档：<https://super.cqvip.com/api-docs/329941873e0>

AI 检索文档：<https://super.cqvip.com/api-docs/493611377e0>

文献详情文档：<https://super.cqvip.com/api-docs/332141435e0>

引用格式文档：<https://super.cqvip.com/api-docs/461931506e0>

官方简单检索文档说明单页最大 10 条，因此客户端固定校验 `1 <= size <= 10`。

## 标准化字段

客户端从维普响应中提取：`id`、`title`、`authorInfo`、`abstr`、`keywordInfo`、`organInfo`、`doi`、`journalInfo`、`year`、`paperLanguage`、`isOa` 和 `isPdf`。

不要把 `isPdf` 当作全文内容，也不要根据空 DOI 推断 DOI。

## 错误处理

| 错误码 | 含义 | 是否可重试 |
|---|---|---|
| `CQVIP_NOT_CONFIGURED` | 运行环境没有 Key | 否 |
| `CQVIP_INVALID_*` | 输入或配置错误 | 否 |
| `CQVIP_HTTP_ERROR` | HTTP 错误 | 仅 429/5xx |
| `CQVIP_NETWORK_ERROR` | 超时或网络失败 | 是 |
| `CQVIP_API_ERROR` | API 明确返回失败 | 否 |
| `CQVIP_INVALID_RESPONSE` | 响应不是有效 JSON | 否 |

客户端最多自动重试两次，并在错误消息中对 Key 做脱敏。
