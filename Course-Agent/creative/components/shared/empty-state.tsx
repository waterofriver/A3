import type { LucideIcon } from "lucide-react"

type EmptyStateProps = {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  action,
  className = "",
  description,
  icon: Icon,
  title,
}: EmptyStateProps) {
  return (
    <div className={`grid place-items-center text-center ${className}`}>
      <div className="max-w-sm">
        <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-slate-50 border border-slate-100 text-slate-500 shadow-sm">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </span>
        <h2 className="mt-4 text-base font-bold text-slate-750 text-slate-700">{title}</h2>
        <p className="mt-2 text-sm text-slate-400">{description}</p>
        {action ? (
          <button
            className="mt-4 inline-flex h-9 items-center justify-center rounded-xl bg-primary px-4 text-sm font-semibold text-white shadow-md shadow-primary/10 transition-all duration-200 hover:bg-blue-600 hover:shadow-lg active:scale-95"
            onClick={action.onClick}
            type="button"
          >
            {action.label}
          </button>
        ) : null}
      </div>
    </div>
  )
}
