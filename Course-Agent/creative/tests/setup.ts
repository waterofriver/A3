import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"
import { afterEach } from "vitest"

class TestResizeObserver implements ResizeObserver {
  constructor(private readonly callback: ResizeObserverCallback) {}

  observe(target: Element) {
    this.callback(
      [
        {
          target,
          contentRect: {
            width: 1024,
            height: 420,
            x: 0,
            y: 0,
            top: 0,
            right: 1024,
            bottom: 420,
            left: 0,
            toJSON: () => ({}),
          },
          borderBoxSize: [{ inlineSize: 1024, blockSize: 420 }],
          contentBoxSize: [{ inlineSize: 1024, blockSize: 420 }],
          devicePixelContentBoxSize: [{ inlineSize: 1024, blockSize: 420 }],
        },
      ],
      this,
    )
  }

  disconnect() {}
  unobserve() {}
}

globalThis.ResizeObserver = TestResizeObserver

afterEach(cleanup)
