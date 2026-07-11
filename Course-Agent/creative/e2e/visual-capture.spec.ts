import fs from "node:fs/promises"
import path from "node:path"

import { expect, test, type Page } from "@playwright/test"

import { seedConfirmedUser } from "./helpers"
import {
  expectNoCriticalA11yViolations,
  expectNoHorizontalOverflow,
} from "./layout-audit"

const screenshotRoot = path.resolve(__dirname, "../../../artifacts/screenshots")

test.use({ trace: "on" })

async function capture(page: Page, filename: string) {
  await page.evaluate(() => document.fonts.ready)
  await expectNoHorizontalOverflow(page)
  await page.evaluate(() => {
    document.querySelectorAll("nextjs-portal").forEach((portal) => {
      const element = portal as HTMLElement
      element.style.setProperty("display", "none", "important")
    })
  })
  await fs.mkdir(screenshotRoot, { recursive: true })
  const image = await page.screenshot({
    animations: "disabled",
    fullPage: true,
    path: path.join(screenshotRoot, filename),
  })
  expect(image.byteLength, `${filename} must not be blank`).toBeGreaterThan(20_000)
  await expectNoCriticalA11yViolations(page)
}

test("captures all delivery states", async ({ context, page }, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-1440",
    "Canonical screenshots use the 1440x900 project.",
  )

  await context.addInitScript(() => {
    window.addEventListener("DOMContentLoaded", () => {
      const style = document.createElement("style")
      style.textContent = "nextjs-portal { display: none !important; }"
      document.head.appendChild(style)
    })
  })

  const userId = `capture-${Date.now()}`
  await page.goto("/login")
  await expect(page.getByRole("heading", { name: "智学引擎" })).toBeVisible()
  await capture(page, "01-login.png")

  await page.getByLabel("用户 ID").fill(userId)
  const userResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/api/user/info"),
  )
  await page.getByRole("button", { name: "进入学习平台" }).click()
  const userResponse = await userResponsePromise
  expect(
    userResponse.ok(),
    `user info failed: ${userResponse.status()} ${await userResponse.text()}`,
  ).toBeTruthy()
  await expect
    .poll(() =>
      page.evaluate(() => window.localStorage.getItem("zhixue_user_id")),
    )
    .toBe(userId)
  await expect(page).toHaveURL(/\/profile$/, { timeout: 30_000 })
  await page
    .getByPlaceholder("介绍你的专业、基础或学习目标")
    .fill("我正在学 ROS2，基础一般，薄弱点是发布订阅与 QoS，喜欢图解和代码。")
  await page.getByRole("button", { name: "发送" }).click()
  await expect(page.getByText("画像抽取Agent")).toBeVisible()
  await capture(page, "02-profile-stream.png")
  await expect(page.getByRole("button", { name: "画像确认完成" })).toBeEnabled()
  await page.getByRole("button", { name: "画像确认完成" }).click()

  await expect(page).toHaveURL(/\/workspace$/)
  await page.getByLabel("课程", { exact: true }).selectOption({ index: 0 })
  await page.getByLabel("薄弱知识点").fill("发布订阅与 QoS")
  await page.getByRole("button", { name: "全选资源" }).click()
  await page.getByRole("button", { name: "生成学习资源" }).click()
  await expect(
    page.getByLabel("Agent 进度").getByText("题库Agent"),
  ).toBeVisible({ timeout: 15_000 })
  await capture(page, "03-workspace-generating.png")
  await expect(page.getByText("全部资源已生成")).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole("link", { name: /查看习题题库/ })).toBeVisible()
  await capture(page, "04-workspace-results.png")

  await page.getByRole("link", { name: /查看习题题库/ }).click()
  await expect(page).toHaveURL(/\/resources\//, { timeout: 30_000 })
  await expect(page.getByText("ROS2 节点通信中", { exact: false })).toBeVisible()
  await capture(page, "05-resource-quiz.png")
  await page.getByLabel("B").check()
  await page.getByRole("button", { name: "提交答案" }).click()
  await expect(page.getByText(/得分/)).toBeVisible()

  await page.getByRole("link", { name: "学习路径" }).click()
  await expect(page.getByText("基础补全")).toBeVisible()
  await capture(page, "06-learning-path.png")

  await page.getByRole("button", { name: "打开智能答疑" }).click()
  await page.getByRole("radio", { name: "图解配图" }).click()
  await page.getByLabel("课程问题").fill("QoS 可靠性策略如何选择？")
  await page.getByRole("button", { name: "发送问题" }).click()
  await expect(page.getByText("等待真实 Agent 返回素材")).toBeVisible()
  await capture(page, "07-qa-drawer.png")
  await page.getByRole("button", { name: "Close" }).click()

  await page.getByRole("link", { name: "学习评估" }).click()
  await expect(page.getByText("理论掌握度")).toBeVisible()
  await expect
    .poll(async () => {
      const bar = await page.locator(".recharts-bar-rectangle path").first().boundingBox()
      return bar?.width ?? 0
    })
    .toBeGreaterThan(20)
  await capture(page, "08-evaluation.png")

  await page.getByRole("link", { name: "课程知识库" }).click()
  await expect(page.getByText("课程资料未同步")).toBeVisible()
  await capture(page, "09-knowledge.png")

  const networkPage = await context.newPage()
  await networkPage.addInitScript((id) => {
    window.localStorage.setItem("zhixue_user_id", id)
  }, userId)
  await networkPage.route("**/api/course/list", (route) => route.abort("failed"))
  await networkPage.goto("/workspace")
  await expect(networkPage.getByText("接口异常")).toBeVisible()
  await capture(networkPage, "10-network-error.png")
  await networkPage.close()

  const failedUser = `failure-${Date.now()}`
  const failurePage = await context.newPage()
  await seedConfirmedUser(failurePage, failedUser)
  await failurePage.route("**/api/resource/generate", (route) =>
    route.fulfill({
      contentType: "application/json",
      status: 202,
      body: JSON.stringify({
        data: { task_id: "failure-task", status: "queued", deduplicated: false },
        trace_id: "capture-trace",
      }),
    }),
  )
  await failurePage.route("**/api/resource/progress/failure-task", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      headers: { "cache-control": "no-cache" },
      status: 200,
      body: [
        "event: agent.started",
        "id: 1",
        `data: ${JSON.stringify({
          event: "agent.started",
          task_id: "failure-task",
          seq: 1,
          trace_id: "capture-trace",
          current_agent: "讲义编写Agent",
          progress: 18,
          resource_type: "handout",
          content: "",
          finish_flag: false,
          resource_ids: [],
          demo_mode: false,
        })}`,
        "",
        "event: task.failed",
        "id: 2",
        `data: ${JSON.stringify({
          event: "task.failed",
          task_id: "failure-task",
          seq: 2,
          trace_id: "capture-trace",
          current_agent: "讲义编写Agent",
          progress: 38,
          resource_type: "handout",
          content: "",
          finish_flag: true,
          resource_ids: [],
          error: {
            code: "UPSTREAM_TIMEOUT",
            message: "远程 Agent 服务响应超时。",
            retryable: true,
          },
          demo_mode: false,
        })}`,
        "",
        "",
      ].join("\n"),
    }),
  )
  await failurePage.goto("/workspace")
  await failurePage.getByLabel("课程", { exact: true }).selectOption({ index: 0 })
  await failurePage.getByRole("checkbox", { name: "讲义文档" }).check()
  await failurePage.getByRole("button", { name: "生成学习资源" }).click()
  await expect(failurePage.getByRole("button", { name: "重试任务" })).toBeVisible()
  await capture(failurePage, "11-agent-failure.png")
  await failurePage.close()
})
