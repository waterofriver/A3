import AxeBuilder from "@axe-core/playwright"
import { expect, type Page } from "@playwright/test"

export async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }))
  expect(metrics.document, `document width ${metrics.document}px`).toBeLessThanOrEqual(
    metrics.viewport,
  )
}

export async function expectNoCriticalA11yViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze()
  const critical = results.violations.filter(
    (violation) => violation.impact === "critical",
  )
  expect(
    critical,
    critical
      .map(
        (violation) =>
          `${violation.id}: ${violation.help} (${violation.nodes.length} nodes)`,
      )
      .join("\n"),
  ).toEqual([])
}

export async function expectStablePage(page: Page) {
  await page.evaluate(() => document.fonts.ready)
  await expectNoHorizontalOverflow(page)
  await expectNoCriticalA11yViolations(page)
}
