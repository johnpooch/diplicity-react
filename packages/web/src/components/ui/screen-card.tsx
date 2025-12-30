import * as React from "react"
import { Card, CardHeader, CardContent } from "./card"
import { cn } from "@/lib/utils"

function ScreenCard({ className, ...props }: React.ComponentProps<typeof Card>) {
  return <Card className={className} {...props} />
}

function ScreenCardHeader({ className, ...props }: React.ComponentProps<typeof CardHeader>) {
  return (
    <CardHeader
      className={cn("p-6", className)}
      {...props}
    />
  )
}

function ScreenCardContent({ className, ...props }: React.ComponentProps<typeof CardContent>) {
  return (
    <CardContent
      className={cn("p-6", className)}
      {...props}
    />
  )
}

export { ScreenCard, ScreenCardHeader, ScreenCardContent }
