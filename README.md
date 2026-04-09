# Deep Researcher

从零实现的「深度思考写作」流水线：

1. 根据用户问题生成多条检索 query  
2. 进行全网搜索（DuckDuckGo）  
3. 抓取网页正文并提炼为研究证据  
4. 基于检索证据调用大模型生成中文文章  

## 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置 `.env`

在项目根目录创建 `.env`（可由 `.env.example` 复制）：

```bash
cp .env.example .env
```

示例：

```env
LLM_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
LLM_API_KEY=your_api_key_here
LLM_MODEL=GLM4.7
LLM_TIMEOUT_SECONDS=60

SEARCH_RESULTS_PER_QUERY=5
MAX_PAGES_TO_READ=8
OUTPUT_DIR=outputs
```

> 你要求的配置（例如大模型 API URL 和 KEY）都放在 `.env` 中。

## 3. 运行

```bash
python3 main.py "请分析 AI Agent 在企业中的落地路径与风险"
```

运行后会在 `outputs/` 生成：

- `article_*.md`：最终文章
- `research_notes_*.md`：检索到的来源与摘要证据

## 4. 项目结构

```text
.
├── main.py
├── requirements.txt
├── .env.example
└── deepresearcher
    ├── config.py      # .env 配置加载
    ├── retriever.py   # 全网检索 + 页面正文抓取
    ├── writer.py      # 组织证据 + 调用 LLM 生成文章
    └── pipeline.py    # 端到端流程编排
```
