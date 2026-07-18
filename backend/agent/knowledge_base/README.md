# 旧版知识库模板说明

本目录保留早期本地 Agent 开发阶段使用的 `knowledge_dag_template.json`，用于理解知识点 DAG 的最小字段结构。它不是当前应用的知识库来源，也不会在后端启动时自动同步。

当前课程、素材、校验脚本和资源索引统一维护在仓库顶层：

```text
knowledge_base/
├── knowledge_dag.json
├── knowledge_dag_template.json
├── materials/<knowledge_point_id>/
├── validate_knowledge_base.py
└── build_knowledge_base.py
```

完整维护方法见[顶层知识库 README](../../../knowledge_base/README.md)。

## 模板字段

旧模板包含课程名称、课程说明和知识点列表：

```json
{
  "course_name": "示例课程",
  "course_description": "课程范围和目标",
  "knowledge_points": [
    {
      "id": "example_point_01",
      "name": "示例知识点",
      "description": "该知识点涵盖的内容",
      "category": "所属模块",
      "prerequisites": [],
      "difficulty": 1,
      "estimated_minutes": 30,
      "tags": ["示例标签"]
    }
  ]
}
```

其中：

- `id` 是唯一标识，也应与素材目录名一致；
- `prerequisites` 引用其他知识点 ID，空数组代表入口节点；
- `difficulty` 使用 1-5 的整数；
- `estimated_minutes` 是正整数分钟数；
- `tags` 用于检索和主题匹配。

## 与当前格式的差异

本目录的历史模板缺少 `course_slug`。顶层校验器要求活动 DAG 提供符合 `^[a-z0-9][a-z0-9-]{0,63}$` 的 `course_slug`，后端也使用它确定 `backend/data/courses/<course_slug>/` 的目标目录。因此，不要把这里的模板直接重命名后作为当前课程 DAG。

如需基于旧模板迁移：

1. 复制字段内容到顶层 `knowledge_base/knowledge_dag_template.json`；
2. 补充 `course_slug` 和真实课程信息；
3. 在顶层 `materials/<knowledge_point_id>/` 放入对应素材；
4. 执行 `python knowledge_base/validate_knowledge_base.py`；
5. 需要资源索引时执行 `python knowledge_base/build_knowledge_base.py`。

新的课程文件、DAG 修改和生成元数据都应写入顶层 `knowledge_base/`，不要在本目录新增运行时资料。
