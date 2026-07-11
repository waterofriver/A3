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
        <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-md bg-[#eef2f7] text-[#66758b]">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </span>
        <h2 className="mt-4 text-base font-semibold text-[#344258]">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-[#748196]">{description}</p>
        {action ? (
          <button
            className="mt-4 inline-flex h-9 items-center justify-center rounded-md bg-[#2457d6] px-4 text-sm font-semibold text-white transition hover:bg-[#1d48b5]"
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
