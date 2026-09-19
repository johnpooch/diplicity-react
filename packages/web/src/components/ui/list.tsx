import { Link } from "react-router"
import { cn } from "@/lib/utils"

interface ListSectionProps {
  header?: React.ReactNode
  children: React.ReactNode
  className?: string
}

function ListSection({ header, children, className }: ListSectionProps) {
  return (
    <section className={cn("flex flex-col gap-2", className)}>
      {header != null &&
        (typeof header === "string" ? (
          <h2 className="text-sm font-medium text-muted-foreground">
            {header}
          </h2>
        ) : (
          header
        ))}
      <ul className="rounded-xl border bg-card">{children}</ul>
    </section>
  )
}

interface ListItemProps {
  leading?: React.ReactNode
  title: React.ReactNode
  subtitle?: React.ReactNode
  trailing?: React.ReactNode
  trailingAction?: React.ReactNode
  href?: string
  onClick?: () => void
  checked?: boolean
  muted?: boolean
  ariaLabel?: string
  className?: string
}

const primaryClassName =
  "flex min-h-11 min-w-0 flex-1 items-center gap-3 px-3 py-3 text-left outline-none focus-visible:z-10 focus-visible:ring-[3px] focus-visible:ring-ring/50"

const interactivePrimaryClassName = cn(primaryClassName, "cursor-pointer")

function ListItem({
  leading,
  title,
  subtitle,
  trailing,
  trailingAction,
  href,
  onClick,
  checked,
  muted,
  ariaLabel,
  className,
}: ListItemProps) {
  const interactive = href != null || onClick != null || checked !== undefined
  const body = (
    <>
      {leading != null && <div className="shrink-0">{leading}</div>}
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "truncate font-semibold leading-tight",
            muted && "text-muted-foreground"
          )}
        >
          {title}
        </p>
        {subtitle != null && (
          <p className="truncate text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {trailing != null && <div className="shrink-0">{trailing}</div>}
    </>
  )

  const primary = href ? (
    <Link
      to={href}
      aria-label={ariaLabel}
      className={cn(interactivePrimaryClassName, "text-inherit no-underline")}
    >
      {body}
    </Link>
  ) : checked !== undefined ? (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={ariaLabel}
      className={interactivePrimaryClassName}
      onClick={onClick}
    >
      {body}
    </button>
  ) : onClick ? (
    <button
      type="button"
      aria-label={ariaLabel}
      className={interactivePrimaryClassName}
      onClick={onClick}
    >
      {body}
    </button>
  ) : (
    <div className={primaryClassName}>{body}</div>
  )

  return (
    <li
      className={cn(
        "relative flex border-b border-border first:rounded-t-[inherit] last:rounded-b-[inherit] last:border-b-0",
        interactive && "transition-colors hover:bg-accent/50",
        className
      )}
    >
      {primary}
      {trailingAction != null && (
        <div className="flex shrink-0 items-center py-3 pr-1.5">
          {trailingAction}
        </div>
      )}
    </li>
  )
}

export { ListSection, ListItem }
