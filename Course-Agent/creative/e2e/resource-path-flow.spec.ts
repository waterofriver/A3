import { expect, test } from "@playwright/test"

import { seedConfirmedUser } from "./helpers"

test("generates resources, submits a quiz, and opens the learning path", async ({
  page,
}) => {
  const userId = `resource-student-${Date.now()}`
  await seedConfirmedUser(page, userId)
  await page.goto("/workspace")

  await page.getByLabel("课程", { exact: true }).selectOption({ index: 0 })
  await page.getByLabel("薄弱知识点").fill("ROS2 节点通信")
  await page.getByRole("button", { name: "全选资源" }).click()
  await page.getByRole("button", { name: "生成学习资源" }).click()

  await expect(
    page.getByLabel("Agent 进度").getByText("题库Agent"),
  ).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText("全部资源已生成")).toBeVisible({ timeout: 30_000 })
  await page.getByRole("link", { name: /习题题库/ }).click()

  await page.getByLabel("B").check()
  await page.getByRole("button", { name: "提交答案" }).click()
  await expect(page.getByText(/得分/)).toBeVisible()

  await page.getByRole("link", { name: "学习路径" }).click()
  await expect(page.getByText("基础补全")).toBeVisible()
})
