# 学习路径箭头续改对话总结

## 用户目标

结束 3000 至 3016 和 8000 端口进程，继续检查学习路径节点前端问题，并使节点按顺序保留箭头指向。

## 处理结果

- 通过 TCP 监听检查确认上述端口均未被占用。
- 根因：学习路径使用自定义 React Flow 节点，但没有 `Handle`，导致相邻边无法在画布中渲染。
- 在每个节点左右补充 target/source 连接锚点；相邻节点继续按 `position` 排序，并增加闭合箭头终点。
- 增加回归测试，验证无序输入也会形成按 `position` 排序的相邻、定向边。

## 验证

- `pnpm test tests/learning-path/learning-path-graph.test.tsx`：6 项通过。
- `pnpm typecheck`：通过。
- 全量 `pnpm lint` 会扫描已有 `.next-immersive-verify` 构建产物并报告预存错误；本次改动文件需要单独 ESLint 验证。
