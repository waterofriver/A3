# 课程知识库搭建与维护指南

`knowledge_base/` 是本项目课程内容的权威源目录。当前已收录高校课程“机器人与安全”（`robot-safety`），以知识点有向无环图（DAG）组织 15 个学习节点，并为每个节点提供讲义、课件、实验文档、视频、代码或拓展阅读。

后端启动时会读取这里的 `knowledge_dag.json`，将 `materials/` 同步到 `backend/data/courses/<course_slug>/`，再建立课程文档索引。因此，课程维护应在本目录完成，不应直接把运行时目录当作源数据修改。

## 目录职责

```text
knowledge_base/
├── knowledge_dag.json               # 当前课程 DAG，运行时权威定义
├── knowledge_dag_template.json      # 新课程或重构 DAG 时的字段模板
├── materials/                       # 按知识点 ID 分组的原始素材
│   └── <knowledge_point_id>/
│       ├── <course files>
│       └── metadata.json            # build 脚本生成，可重新生成
├── resource_index.json              # build 脚本生成的全局资源清单
├── validate_knowledge_base.py       # DAG、依赖和素材完整性校验
└── build_knowledge_base.py          # 生成 metadata 和 resource_index
```

| 文件或目录 | 是否手工维护 | 作用 |
|---|---:|---|
| `knowledge_dag.json` | 是 | 定义课程信息、知识点属性和先修关系 |
| `materials/` | 是 | 保存课程原始资料，目录名必须与知识点 ID 一致 |
| `metadata.json` | 否 | 描述单个知识点下的文件、类型、大小和可预览状态 |
| `resource_index.json` | 否 | 汇总整个课程的资源路径、类型与知识点归属 |
| `backend/data/courses/` | 否 | 后端启动时生成或更新的运行时副本 |

## 当前课程内容

当前 `knowledge_dag.json` 的课程名为“机器人与安全”，`course_slug` 为 `robot-safety`，包含以下 15 个节点：

| ID | 知识点 | 模块 | 难度 | 建议时长 |
|---|---|---|---:|---:|
| `course_orientation` | 课程导论与实验总览 | 基础准备 | 1 | 30 分钟 |
| `vm_environment_setup` | 虚拟机与实验环境配置 | 基础准备 | 1 | 45 分钟 |
| `network_environment_setup` | 网络环境与基础连通性 | 基础准备 | 2 | 40 分钟 |
| `exp01_ros_turtlesim` | 实验一：ROS 进阶与小乌龟 | ROS 基础 | 2 | 60 分钟 |
| `exp02_robot_remote_control` | 实验二：机器人连接与远程控制 | ROS 基础 | 2 | 60 分钟 |
| `exp03_slam_mapping_navigation` | 实验三：SLAM 地图构建与导航 | 移动与导航 | 3 | 90 分钟 |
| `exp04_line_following` | 实验四：机器人循线跟踪 | 移动与导航 | 3 | 75 分钟 |
| `exp05_arp_poisoning` | 实验五：ARP 中毒攻击 | 网络攻防 | 3 | 60 分钟 |
| `exp06_mitm_attack` | 实验六：中间人攻击 | 网络攻防 | 3 | 75 分钟 |
| `exp07_dos_attack` | 实验七：DOS 攻击 | 网络攻防 | 3 | 60 分钟 |
| `exp08_rsa_communication` | 实验八：RSA 加密与通讯 | 密码与通信 | 3 | 80 分钟 |
| `exp09_stereo_vision_attack` | 实验九：双目视觉摄像头识别攻击 | 视觉与安全 | 4 | 80 分钟 |
| `exp10_brute_force_attack` | 实验十：暴力破解攻击 | 网络攻防 | 3 | 60 分钟 |
| `exp11_multi_robot_formation` | 实验十一：多机编队实验 | 综合实验 | 4 | 90 分钟 |
| `shared_references` | 课程拓展阅读与参考资料 | 拓展资源 | 1 | 30 分钟 |

这些节点同时覆盖环境准备、ROS 与机器人控制、移动导航、网络攻防、密码通信、视觉安全和综合协同实验。DAG 不只是目录清单，学习路径规划、知识状态展示和资源检索都可使用其中的依赖、难度、时长和标签信息。

## DAG 设计

DAG（Directed Acyclic Graph，有向无环图）用于表达“学习某知识点前需要掌握哪些内容”。例如：

```text
课程导论
  └─> 虚拟机配置
       └─> 网络环境配置
            ├─> ROS 小乌龟 -> 远程控制 -> SLAM -> 循线跟踪 ─┐
            └─> ARP 攻击 -> 中间人 -> DOS -> RSA -> 视觉攻击 -> 暴力破解 ─┤
                                                                         └─> 多机编队
```

实际关系以 `knowledge_dag.json` 为准。设计新节点时，建议将一个节点控制在约 30-90 分钟的学习量，并确保依赖表达的是必要先修知识，而不是简单的章节顺序。

### 顶层字段

| 字段 | 类型 | 要求 |
|---|---|---|
| `course_name` | string | 非空课程全称，前端和索引会使用 |
| `course_slug` | string | 非空；只允许小写字母、数字和连字符，最长 64 字符 |
| `course_description` | string | 课程范围与培养目标的简要说明 |
| `knowledge_points` | array | 非空知识点列表 |

### 知识点字段

| 字段 | 类型 | 要求 |
|---|---|---|
| `id` | string | 全课程唯一，同时作为 `materials/` 子目录名 |
| `name` | string | 前端显示名称，不能为空 |
| `description` | string | 说明该节点的学习内容与目标 |
| `category` | string | 所属章节或能力模块 |
| `prerequisites` | string[] | 前置知识点 ID；入口节点使用空数组 |
| `difficulty` | integer | 1-5，分别表示入门到高阶 |
| `estimated_minutes` | integer | 正整数，建议学习时长（分钟） |
| `tags` | string[] | 非空检索标签列表 |

合法的最小示例：

```json
{
  "course_name": "示例课程",
  "course_slug": "example-course",
  "course_description": "介绍示例课程的知识范围与学习目标。",
  "knowledge_points": [
    {
      "id": "foundation",
      "name": "基础知识",
      "description": "建立后续学习所需的基本概念。",
      "category": "基础模块",
      "prerequisites": [],
      "difficulty": 1,
      "estimated_minutes": 30,
      "tags": ["基础", "入门"]
    }
  ]
}
```

### 依赖规则

- 所有 `id` 必须唯一。
- `prerequisites` 必须引用同一份 DAG 中真实存在的 ID，不能写显示名称。
- 至少有一个 `prerequisites: []` 的入口节点。
- 依赖关系不能形成环，例如 A 依赖 B、B 又依赖 A。
- 每个知识点都必须存在同名素材目录，并至少包含一份校验器支持的文件。

## 素材组织与格式

每个知识点使用独立目录：

```text
materials/
├── exp01_ros_turtlesim/
│   ├── 10_实验一 ROS进阶—玩转小乌龟.docx
│   ├── 11_实验一 ROS进阶—玩转小乌龟.pptx
│   ├── 实验一 ROS进阶—玩转小乌龟演示视频.mp4
│   └── turtlesim.py
└── shared_references/
    ├── ROS基础（课外阅读）.pdf
    └── Turtlebot3京天用户手册v3.1.docx
```

`validate_knowledge_base.py` 将以下扩展名视为可满足“至少一份素材”的受支持格式：

```text
.docx  .pptx  .pdf  .md  .txt  .mp4  .png  .jpg  .jpeg  .webp
```

`build_knowledge_base.py` 还会为代码、其他视频或图片、压缩包等文件分类并写入索引，例如 `.py`、`.js`、`.webm`、`.gif`、`.zip`。这类附加文件可以作为实操或补充资源，但若某个目录只有这些文件，当前校验器仍会判定缺少受支持素材。

文件名可以使用中文或英文；目录名必须使用对应知识点 `id`。`metadata.json` 由脚本生成，不计作课程原始素材。

## 维护流程

### 1. 修改 DAG 与素材

1. 在 `knowledge_dag.json` 新增、调整或删除知识点。
2. 在 `materials/<knowledge_point_id>/` 放入对应课程资料。
3. 检查目录名、知识点 ID 和 `prerequisites` 是否一致。

创建全新 DAG 时可复制 `knowledge_dag_template.json`，删除示例节点后填写真实数据。不要直接采用 `backend/agent/knowledge_base/` 下的旧模板；该模板仅为历史兼容参考，缺少当前顶层 DAG 所需的 `course_slug`。

### 2. 校验知识库

在本目录执行：

```bash
cd knowledge_base
python validate_knowledge_base.py
```

成功结果为：

```text
校验通过
```

校验内容包括 JSON 格式、必填字段、slug 规则、ID 唯一性、前置引用、循环依赖、入口节点、难度与时长范围、素材目录及受支持文件。

### 3. 生成资源元数据

```bash
python build_knowledge_base.py
```

脚本会重建：

- 每个知识点目录的 `metadata.json`；
- 顶层 `resource_index.json`。

生成信息包括文件路径、扩展名、资源类型、大小、知识点归属、是否可检索和是否支持预览。它们用于增强资源检索和后续 RAG 扩展，但不是后端启动的前置条件。

### 4. 触发运行时同步

后端 FastAPI 应用启动时会：

1. 读取顶层 `knowledge_dag.json`；
2. 将每个素材目录增量复制到 `backend/data/courses/<course_slug>/`；
3. 生成运行时 `course.json`；
4. 由 `CourseIndexer` 建立可供课程 API 使用的文档索引。

当前课程的目标目录为 `backend/data/courses/robot-safety/`。同步按文件大小和修改时间跳过未变化文件，但不会自动删除目标目录中源端已经移除的旧文件；若调整或删除素材，应额外检查运行时目录后再交付。

## 大文件与版本控制

课程视频和参考书可能接近代码托管平台的单文件限制。GitHub 普通 Git 对超过 50 MiB 的文件会给出警告，并拒绝超过 100 MiB 的单文件；本仓库当前课程素材已控制在 100 MiB 以下，但仍应在新增资源前检查大小。

```powershell
Get-ChildItem materials -File -Recurse |
  Sort-Object Length -Descending |
  Select-Object -First 20 FullName, Length
```

对于较大的视频或数据集，优先压缩、拆分或使用团队已配置的 Git LFS/对象存储方案。当前仓库没有 `.gitattributes` 中的 Git LFS 规则，不应仅安装 Git LFS 就假设大文件会自动被追踪。比赛离线提交时还要确认外部对象已实际打包，不能只提交失效链接或 LFS 指针。

## 交付检查清单

- [ ] `course_name`、`course_slug` 和课程描述准确。
- [ ] 知识点 ID 唯一，字段完整，难度和时长合法。
- [ ] 每个前置依赖都存在，至少有一个入口节点，DAG 无环。
- [ ] 每个知识点有同名素材目录和至少一份受支持素材。
- [ ] `python validate_knowledge_base.py` 输出“校验通过”。
- [ ] 需要更新索引时已执行 `python build_knowledge_base.py`。
- [ ] 后端重启后，`backend/data/courses/<course_slug>/` 与源素材一致。
- [ ] 新增文件未超过代码托管和比赛打包限制。
- [ ] 涉及教材、论文、视频或开源代码时，已确认授权、来源和许可证标注。
- [ ] 前端课程列表、资源预览和学习路径能读取新增内容。

## 常见问题

**为什么顶层和后端目录都有课程文件？**

顶层 `knowledge_base/` 是维护和提交的源目录；`backend/data/courses/` 是为现有课程索引器准备的运行时副本。后者可由启动同步更新，不应作为唯一资料来源。

**一个知识点可以有多个前置吗？**

可以。直接在数组中列出多个 ID，例如 `"prerequisites": ["ros_basics", "network_basics"]`。

**确实需要交替学习，如何避免循环依赖？**

把内容拆为阶段节点，例如“动力学（基础）”和“动力学（进阶）”，再建立单向依赖。DAG 必须保持无环，才能稳定进行路径排序。

**是否必须建立 `parsed/` 目录？**

不需要。当前系统直接同步原始文件并由课程索引器提取可预览文本。只有后续引入独立的文本清洗、切片或向量化流水线时，才需要设计额外的派生目录。

**为什么新增代码文件后校验仍可能失败？**

构建脚本可以索引代码文件，但校验器用于保证每个教学节点至少有一份讲义、课件、文本、视频或图片。请同时放入校验器支持的课程素材，或在明确评估影响后扩展校验器规则。
