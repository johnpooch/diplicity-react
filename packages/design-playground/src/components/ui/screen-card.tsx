import * as React from "react"
import { cn } from "@/lib/utils"

function ScreenCard({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex flex-col",
        "py-2",
        "@[500px]:rounded-xl @[500px]:border @[500px]:bg-card @[500px]:py-6 @[500px]:shadow-sm",
        className
      )}
      {...props}
    />
  )
}

function ScreenCardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("px-0 @[500px]:px-6", className)}
      {...props}
    />
  )
}

function ScreenCardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("px-0 @[500px]:px-6", className)}
      {...props}
    />
  )
}

export { ScreenCard, ScreenCardHeader, ScreenCardContent }
