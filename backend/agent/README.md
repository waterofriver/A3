# 智学引擎 — Agent 使用手册

> 本文档面向**前后端开发者**，介绍 Agent 引擎的组成、功能和集成方式。
> 你不需要修改 Agent 代码，只需按本文档完成配置和对接。

---

## 一、Agent 引擎概览

Agent 引擎位于 `A3/backend/agent/`，是智学引擎的 AI 核心。它基于 DeepSeek API 驱动，对外暴露 Python 接口，由后端 FastAPI 网关调用。

```
agent/
├── config.py                  ← DeepSeek API 配置（.env）
├── requirements.txt           ← Python 依赖
├── models/schemas.py          ← 统一数据模型（所有 Agent 共享）
├── utils/
│   ├── llm_client.py          ← DeepSeek API 封装（同步/异步/重试）
│   ├── json_parser.py         ← LLM 输出 → 结构化 JSON
│   ├── dag_loader.py          ← 知识 DAG 加载
│   └── material_loader.py     ← 课件材料提取（PDF/DOCX/PPTX/TXT）
├── profile_agent/             ← Agent 1: 画像构建
├── planner/                   ← Agent 2: 学习路径规划
├── supervisor/                ← Agent 3: 会话调度
├── doc_agent/                 ← Agent 4: 讲义文档生成
├── mindmap_agent/             ← Agent 5: 思维导图生成
├── quiz_agent/                ← Agent 6: 练习题生成
├── video_agent/               ← Agent 7: 视频推送 + 导览脚本
└── reference_agent/           ← Agent 8: 拓展阅读推荐
```

---

## 二、八个 Agent 功能一览

### Agent 1：ProfileAgent（画像构建）

| 项目 | 说明 |
|---|---|
| 功能 | 从学生自由对话中提取 6 维度学习画像 |
| 输入 | 学生聊天文本 + 已有画像（增量更新） |
| 输出 | `StudentProfile`（知识基础、认知风格、学习目标、薄弱环节、学习节奏、兴趣偏好） |
| 调用方 | Supervisor → 后端 `/api/chat/profile` |
| 前端展示 | [画像采集页](A3/Course-Agent/creative/app/(platform)/profile/page.tsx) — 聊天式对话界面 |

### Agent 2：PlannerAgent（学习路径规划）

| 项目 | 说明 |
|---|---|
| 功能 | 根据学生画像 + 知识 DAG，Kahn 拓扑排序 + LLM 生成个性化学习路径 |
| 输入 | `StudentProfile` + `KnowledgeDAG`（从 A3/knowledge_base/ 加载） |
| 输出 | `LearningPath`（有序知识点列表，每项含学习深度/时长/资源类型推荐） |
| 调用方 | Supervisor → 后端 `/api/path/get` |
| 前端展示 | [学习路径页](A3/Course-Agent/creative/app/(platform)/path/page.tsx) — ReactFlow 可视化 |

### Agent 3：Supervisor（会话调度）

| 项目 | 说明 |
|---|---|
| 功能 | 意图分类 → Agent 分发 → SessionState 管理 |
| 输入 | 用户文本 + `SessionState` |
| 输出 | `SupervisorResult`（意图标签 + 用户回复 + 更新后的 SessionState） |
| 调用方 | 后端 Profile/Chat 路由 |
| 支持意图 | extract_profile / plan_path / answer_question / generate_resource / evaluate / chitchat |

### Agent 4：DocAgent（讲义文档生成）

| 项目 | 说明 |
|---|---|
| 功能 | 基于课件材料和画像生成结构化讲义文档 |
| 输入 | `KnowledgePoint` + `StudentProfile` + 课件文本（MaterialLoader） |
| 输出 | `ResourceOutput { DocContent }`（3-6 章节，每章含 heading/body_markdown/key_points） |
| 调用方 | 后端资源生成流 `/api/resource/generate`（`handout` 类型） |
| 前端展示 | [资源工作台](A3/Course-Agent/creative/app/(platform)/workspace/page.tsx) — Markdown 渲染 |

**后端对接要点**：DocAgent 返回的 `content.sections` 是章节列表，后端需要拼接为单个 Markdown 字符串存入 `payload.markdown`，前端用 `react-markdown` 渲染。

### Agent 5：MindMapAgent（思维导图生成）

| 项目 | 说明 |
|---|---|
| 功能 | 基于课件材料生成结构化思维导图（含 Mermaid 语法） |
| 输入 | `KnowledgePoint` + `StudentProfile` + 课件文本 |
| 输出 | `ResourceOutput { MindMapContent }`（root_topic + mermaid_code + nodes 树） |
| 调用方 | 后端资源生成流 `/api/resource/generate`（`mindmap` 类型） |
| 前端展示 | [资源工作台](A3/Course-Agent/creative/app/(platform)/workspace/page.tsx) — Mermaid 渲染或自定义组件 |

**后端对接要点**：`content.nodes` 是 `[{id, label, parent_id, children}]` 格式，可直接传给前端的思维导图组件。`content.mermaid_code` 是一段 Mermaid mindmap 语法的字符串，可粘贴到 [mermaid.live](https://mermaid.live) 预览。

### Agent 6：QuizAgent（练习题生成）

| 项目 | 说明 |
|---|---|
| 功能 | 基于课件材料和画像生成个性化练习题（单选/多选/判断/简答） |
| 输入 | `KnowledgePoint` + `StudentProfile` + 课件文本 + `question_count`（5-10） |
| 输出 | `ResourceOutput { QuizContent }`（8 道题，题型混合，每道题含 stem/options/answer/explanation） |
| 调用方 | 后端资源生成流 `/api/resource/generate`（`quiz` 类型） |
| 前端展示 | [资源工作台](A3/Course-Agent/creative/app/(platform)/workspace/page.tsx) — 答题卡片 |

**后端对接要点**：每道题的 `options` 格式为 `["A. 选项A", "B. 选项B", ...]`，`correct_answer` 为 `"A"` 或 `"ABD"`（多选）。后端转换为 API 格式时需注意 `question_type` 映射：`single_choice / multiple_choice / true_false / short_answer`。

### Agent 7：VideoAgent（视频推送 + 导览脚本）

| 项目 | 说明 |
|---|---|
| 功能 | 扫描知识点素材目录找到 MP4 文件 → LLM 生成个性化视频导览脚本（5 段分镜 + 推送理由） |
| 输入 | `KnowledgePoint` + `StudentProfile` + 课件文本 + `materials_dir`（素材目录路径） |
| 输出 | `VideoResult { has_video, video_path, push_reason, resource { VideoScriptContent } }` |
| 调用方 | 后端资源生成流 `/api/resource/generate`（`video` 类型） |
| 前端展示 | [资源工作台](A3/Course-Agent/creative/app/(platform)/workspace/page.tsx) — 视频播放器 + 导览章节 |

#### ⚠️ 后端对接必读

VideoAgent **不会返回可直接播放的 URL**。它返回的是：

```
VideoResult:
  video_path       = "/path/to/A3/knowledge_base/materials/exp05_arp_poisoning/实验五 ARP中毒演示视频.mp4"
  video_duration   = 360  (秒)
  has_video        = true / false
  push_reason      = "推荐理由文本..."
  resource.content.scenes = [{ narration, visual_description, duration_seconds }, ...]
```

**后端需要做的事**（参考 `A3/backend/app/agents/real.py` 中的实现）：

1. 将 `video_path` 从磁盘绝对路径转换为前端可访问的 HTTP URL
2. 构造 `media_url`，例如 `/media/{kp_id}/{video_filename}`
3. 在 SSE 事件的 `resource.ready` 中设置 `media_url`
4. 前端拿到 `media_url` 后在 `<video src={media_url}>` 中播放

示例代码：
```python
# 在 AgentProvider 实现中
import os, shutil
video_name = os.path.basename(result.video_path)
media_url = f"/media/{knowledge_point.id}/{video_name}"

# 将 MP4 复制/链接到静态资源目录
static_dir = Path("./static/media") / knowledge_point.id
static_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(result.video_path, static_dir / video_name)
```

**前端对接要点**：VideoAgent 返回的分镜列表 `scenes` 可以直接用作视频播放器的章节导航，每个分镜的 `duration_seconds` 可用于跳转到对应时间点。

### Agent 8：ReferenceAgent（拓展阅读推荐）

| 项目 | 说明 |
|---|---|
| 功能 | 从课程拓展阅读库 + 外部经典读物中，根据学生画像和当前知识点推荐最匹配的阅读材料 |
| 输入 | `KnowledgePoint` + `StudentProfile` + `shared_refs_summary`（MaterialLoader 提供） |
| 输出 | `ReferenceResult { library_recommendations[], external_recommendations[], reading_path }` |
| 调用方 | 后端资源生成流 `/api/resource/generate`（`handout` 类型，暂归类为文档） |
| 前端展示 | [资源工作台](A3/Course-Agent/creative/app/(platform)/workspace/page.tsx) — 阅读卡片列表 |

#### ⚠️ 后端对接必读

ReferenceAgent 的推荐结果是 **两个独立列表**（不在 `resource.content` 中，因为 Pydantic 类型约束）：

```
ReferenceResult:
  library_recommendations: [
    { title, source: "in_library", file_path, relevance_reason, suggested_focus, priority }
  ]
  external_recommendations: [
    { title, source: "external", author, relevance_reason, suggested_focus, priority }
  ]
  reading_path: "建议阅读顺序..."
```

`file_path` 是磁盘绝对路径（如 `/path/to/shared_references/ROS基础.pdf`），后端需要将其转为前端可访问的 URL。

---

## 三、5 类资源类型与 Agent 对应关系

前端请求 `resource_type_list` 时使用以下枚举值：

| 前端 resource_type | 对应 Agent | 说明 |
|---|---|---|
| `handout` | DocAgent / ReferenceAgent | 讲义文档 或 拓展阅读推荐 |
| `mindmap` | MindMapAgent | 思维导图 |
| `quiz` | QuizAgent | 练习题 |
| `code` | *未接入* | 代码案例（待开发） |
| `video` | VideoAgent | 视频推送 + 导览 |

---

## 四、环境配置

### 后端 .env（FastAPI 网关）

在 `A3/.env`（从根目录 `.env.example` 复制）：

```bash
# Agent 模式（使用本地 Agent 引擎时选 local）
AGENT_MODE=mock          # mock=演示模式 | local=真实引擎 | remote=远程服务

# 知识库路径（相对于 backend/ 目录）
KNOWLEDGE_BASE_ROOT=../knowledge_base

# 数据库
DATABASE_URL=sqlite:///./data/zhixue.db

# CORS
WEB_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Agent .env（AI 引擎）

在 `A3/.env`：

```bash
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
DEEPSEEK_TIMEOUT=120
DEEPSEEK_MAX_RETRIES=3
```

### 系统依赖

```bash
# Ubuntu 24.04
sudo apt update
sudo apt install ffmpeg -y    # VideoAgent 需要 ffprobe 读视频时长

# Python 依赖
cd A3/backend
pip install -r agent/requirements.txt
```

---

## 五、后端集成指南

### 方式 A：使用 RealAgentProvider（推荐）

1. 在 `A3/backend/app/agents/real.py` 中已有 `RealAgentProvider` 实现（需要复制回来或重新创建）
2. 在 `A3/backend/app/api/dependencies.py` 中注册 `"local"` 模式
3. 在 `A3/backend/app/core/config.py` 中添加 `"local"` 到 `agent_mode`
4. 在 `A3/.env` 中设置 `AGENT_MODE=local` 和 `DEEPSEEK_API_KEY`

### 方式 B：直接调用

```python
from agent.doc_agent import DocAgent
from agent.utils.material_loader import MaterialLoader

loader = MaterialLoader("../knowledge_base")
kp = loader.load_dag().knowledge_points[0]

result = DocAgent().generate(kp, student_profile, material_context=loader.get_context(kp.id))
```

### 关键转换函数

Agent 引擎使用自己的数据模型（`agent.models.StudentProfile` 等），后端网关使用 API Schema（`app.schemas.profile.StudentProfileData` 等）。两者格式不同，需要在 AgentProvider 中做转换。

参考 `A3/backend/app/agents/real.py` 中的 `_api_profile_to_agent()` 函数。

---

## 六、前端对接要点

### 资源详情 API 返回格式

前端调用 `GET /api/resource/detail/{resource_id}` 后按 `resource_type` 解析：

| resource_type | payload 字段 | 渲染组件 |
|---|---|---|
| `handout` | `{ "markdown": "..." }` | `react-markdown` |
| `mindmap` | `{ "nodes": [{id, label, parent_id}] }` | 自定义树组件 或 Mermaid |
| `quiz` | `{ "questions": [{id, question_type, prompt, options, answer, explanation}] }` | 答题卡片 |
| `video` | `{ "summary", "poster_url", "duration_seconds" }` + `media_url` | `<video>` 播放器 |
| `code` | `{ "language", "code", "description" }` | 代码高亮组件 |

### VideoAgent 前端渲染

VideoAgent 的分镜/导览脚本暂不在标准 API 格式中（API 的 video payload 只有 summary/duration_seconds），建议通过以下方式传递：

1. 后端在 video 资源的 `payload` 中增加 `scenes` 字段
2. 前端读取 `scenes` 渲染为视频章节导航条，支持点击跳转到对应时间

---

## 七、测试

### Mock 测试（无需 API Key，秒级完成）

```bash
cd A3/backend

python -m agent.profile_agent.test_profile_agent     # 14 项
python -m agent.planner.test_planner                 # 14 项
python -m agent.supervisor.test_supervisor           # 19 项
python -m agent.doc_agent.test_doc_agent             # 12 项
python -m agent.mindmap_agent.test_mindmap_agent     # 12 项
python -m agent.quiz_agent.test_quiz_agent           # 12 项
python -m agent.video_agent.test_video_agent         # 11 项
python -m agent.reference_agent.test_reference_agent # 10 项

# 全部 104 项，应全部通过
```

### 真实 LLM 测试（需要 API Key）

```bash
cd A3/backend
# 自行编写调用脚本，例如：
python -c "
from agent.doc_agent import DocAgent
from agent.utils.material_loader import MaterialLoader
loader = MaterialLoader('../knowledge_base')
dag = loader.load_dag()
kp = dag.get_by_id('exp01_ros_turtlesim')
result = DocAgent().generate(kp, material_context=loader.get_context(kp.id))
print('章节数:', len(result.resource.content.sections))
"
```

---

## 八、常见问题

### Q: VideoAgent 返回 `has_video=false`？
A: 该知识点在 `A3/knowledge_base/materials/{kp_id}/` 中没有 `.mp4` 文件。这是正常的——目前 15 个知识点中有 6 个有视频（实验一至六）。

### Q: 启动后端时卡住？
A: 首次启动时需要同步知识库（约 18 秒），运行 `python setup_data.py` 预处理即可。

### Q: PyMuPDF 导入失败？
A: `pip install PyMuPDF`，或系统缺少 `libmupdf`。可用 `pip install pypdf` 作为轻量替代。

### Q: GBK 编码错误？
A: 已修复——Agent 代码已移除 Windows 专用编码逻辑，使用 `utf-8 → utf-16 → latin-1` 编码链。

### Q: 如何对接到我自己的 AgentProvider？
A: 参考 `A3/backend/app/agents/base.py` 中的 `AgentProvider` 抽象类，实现 `stream_profile`、`stream_resources`、`build_learning_path` 等方法，在方法内调用对应的 Agent。
