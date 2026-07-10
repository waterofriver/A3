import { ArrowRight, Sparkles } from "lucide-react"
import Link from "next/link"

export default function WorkspacePage() {
  return (
    <div className="mx-auto w-full max-w-[1360px]">
      <header className="flex items-end justify-between border-b pb-6">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">RESOURCE STUDIO</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">资源工作台</h1>
        </div>
        <span className="rounded-md bg-[#eaf4d0] px-3 py-1.5 text-xs font-semibold text-[#4f6f16]">
          画像驱动
        </span>
      </header>

      <section className="mt-8 grid grid-cols-[minmax(0,1fr)_320px] gap-6">
        <div className="flex min-h-[420px] flex-col items-center justify-center rounded-lg border border-dashed border-[#c7d2e2] bg-white px-12 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-md bg-[#edf3ff] text-[#2457d6]">
            <Sparkles aria-hidden="true" className="h-7 w-7" />
          </span>
          <h2 className="mt-5 text-lg font-semibold text-[#27344a]">暂无资源任务</h2>
          <p className="mt-2 text-sm text-[#718096]">当前课程尚未生成个性化学习资源。</p>
          <Link
            className="mt-6 inline-flex h-10 items-center gap-2 rounded-md bg-[#2457d6] px-4 text-sm font-semibold text-white transition hover:bg-[#1d48b5]"
            href="/profile"
          >
            查看学生画像
            <ArrowRight aria-hidden="true" className="h-4 w-4" />
          </Link>
        </div>

        <aside className="border-l pl-6">
          <p className="text-sm font-semibold text-[#27344a]">任务概览</p>
          <dl className="mt-5 space-y-5">
            <div className="border-b pb-4">
              <dt className="text-xs text-[#7a8799]">运行中</dt>
              <dd className="mt-1 text-2xl font-semibold text-[#182132]">0</dd>
            </div>
            <div className="border-b pb-4">
              <dt className="text-xs text-[#7a8799]">已完成资源</dt>
              <dd className="mt-1 text-2xl font-semibold text-[#182132]">0</dd>
            </div>
            <div>
              <dt className="text-xs text-[#7a8799]">当前 Agent</dt>
              <dd className="mt-2 text-sm font-medium text-[#526279]">等待任务</dd>
            </div>
          </dl>
        </aside>
      </section>
    </div>
  )
}
