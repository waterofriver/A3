import { expect, test } from "@playwright/test"

import { seedConfirmedUser } from "./helpers"
import { expectStablePage } from "./layout-audit"

test("runs the complete learning workflow without desktop overflow", async ({
  page,
}, testInfo) => {
  const userId = `full-${testInfo.project.name}-${Date.now()}`
  await seedConfirmedUser(page, userId)

  await page.goto("/workspace")
  await expect(page.getByRole("heading", { name: "资源工作台" })).toBeVisible()
  await expectStablePage(page)

  await page.getByLabel("课程", { exact: true }).selectOption({ index: 0 })
  await page.getByLabel("薄弱知识点").fill("ROS2 发布订阅与 QoS")
  await page.getByRole("button", { name: "全选资源" }).click()
  await page.getByRole("button", { name: "生成学习资源" }).click()
  await expect(page.getByLabel("资源任务进度")).toBeVisible()
  await expectStablePage(page)
  await expect(page.getByText("全部资源已生成")).toBeVisible({ timeout: 30_000 })

  await page.getByRole("link", { name: /查看习题题库/ }).click()
  await expect(page).toHaveURL(/\/resources\//, { timeout: 30_000 })
  await expect(page.getByRole("heading", { name: "学习资源详情" })).toBeVisible()
  await expectStablePage(page)
  await page.getByLabel("B").check()
  await page.getByRole("button", { name: "提交答案" }).click()
  await expect(page.getByText(/得分/)).toBeVisible()

  await page.getByRole("link", { name: "学习路径" }).click()
  await expect(page.getByText("基础补全")).toBeVisible()
  await expectStablePage(page)

  await page.getByRole("button", { name: "打开智能答疑" }).click()
  await page.getByLabel("课程问题").fill("发布订阅如何解耦？")
  await page.getByRole("button", { name: "发送问题" }).click()
  await expect(page.getByText("发布者负责发送消息", { exact: false })).toBeVisible()
  await expectStablePage(page)
  await page.getByRole("button", { name: "Close" }).click()

  await page.getByRole("link", { name: "学习评估" }).click()
  await expect(page.getByText("理论掌握度")).toBeVisible()
  await expectStablePage(page)

  await page.getByRole("link", { name: "课程知识库" }).click()
  await expect(page.getByText("课程资料未同步")).toBeVisible()
  await expectStablePage(page)
})
