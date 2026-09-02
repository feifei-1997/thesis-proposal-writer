---
name: thesis-proposal-writer
description: 为本科、硕士或博士论文撰写开题报告；先通过普通 Assistant 对话补齐学位层级、专业背景、研究子方向和交付格式，再检索真实文献并生成结构完整、可追溯的开题材料。用于“写开题报告”“完善开题材料”“根据研究方向生成开题”等请求，不用于仅检索论文或通用论文润色。
---

# 论文开题写作

完成一份符合用户学位层级、专业背景和研究条件的开题报告。维普 CQVIP 是本 Skill 的内部文献证据工具，不把它作为独立 Skill 呈现，也不要求用户选择检索供应商。

## 对话状态流

1. 先从当前消息和可见对话历史提取 `topic`、`degree_level`、`major_background`、`research_subdirection`、`deliverable_format`。已回答的信息不得重复询问。
2. 有缺项时，调用 `runner.py` 的 `prepare_proposal`，把返回的 `response` 作为普通 Assistant 文本回复用户，然后结束本轮。不得使用弹窗、表单、中断工具或工具选择框。
3. 初次缺少四项信息时，应在同一条回复里一次询问：
   - 学位层级；
   - 用户的学位专业背景；
   - 研究的具体子方向；
   - 最终交付文件格式。
4. 用户补充后，结合历史答案构造完整的 `proposal_brief` 再次调用；不要只传用户最后一条消息。
5. 只有返回 `status=ready_to_write` 后才撰写正文。

## 调用方式

将 JSON 通过标准输入传给 `python runner.py`：

```json
{
  "action": "prepare_proposal",
  "proposal_brief": {
    "topic": "基于深度学习的电池包寿命研究",
    "degree_level": "专业硕士",
    "major_background": "车辆工程",
    "research_subdirection": "融合工况与温度特征的电池包RUL预测，拟比较LSTM与Transformer",
    "deliverable_format": "Markdown"
  },
  "max_papers": 12,
  "include_citations": true
}
```

也可把输入保存为 UTF-8 JSON 后运行 `python runner.py --input request.json`。只解析标准输出中的 JSON。

## 文献检索与证据规则

- 完整 brief 会触发内部维普检索：先做主题词检索，再做结合子方向的 AI 检索，并按 DOI、文献 ID、标题依次去重。
- 国内外研究现状、具体学者观点和参考文献只能使用 `literature_evidence.papers` 或接口返回的引用格式；不得补造作者、题名、期刊、年份或 DOI。
- 接口返回的是元数据或摘要时，只能表述为“根据题录/摘要”，不得声称已阅读全文。
- `literature_evidence.status=unavailable` 或 `failed` 时仍可撰写不依赖引文的章节，但必须明确说明实时文献检索不可用；参考文献部分保留待检索提示，不得生成占位论文。


需要检查接口、字段或错误处理时，再读取 [references/cqvip_api.md](references/cqvip_api.md)。需要确定正文结构和各部分证据边界时，读取 [references/proposal_structure.md](references/proposal_structure.md)。

## 正文生成

根据 `proposal_brief`、检索证据和学校模板撰写，至少覆盖：研究背景与意义、国内外研究现状、研究目标与主要内容、关键问题、研究方法与技术路线、创新点、可行性分析、进度安排、预期成果和参考文献。

- 研究内容应具体到对象、数据、变量、模型、实验与评价指标；未知条件明确写成待确认项，不擅自承诺已有设备或数据。
- 创新点使用审慎措辞，区分“拟创新”与已经证实的创新。
- 技术路线要与研究目标逐项对应，可用 Mermaid 或编号流程表达。
- 按用户要求输出 Markdown、LaTeX 或可下载文件；用户提供学校模板时优先遵循模板。
- 输出前检查正文引文与参考文献一一对应，并注明文献来源为维普检索结果。
