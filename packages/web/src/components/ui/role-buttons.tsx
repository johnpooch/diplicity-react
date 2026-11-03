import * as React from "react"
import { Slot } from "@radix-ui/react-slot"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type RoleButtonProps = Omit<
  React.ComponentProps<typeof Button>,
  "variant" | "size"
>

type IconRoleButtonProps = Omit<RoleButtonProps, "aria-label"> & {
  "aria-label": string
}

interface SecondaryButtonProps extends RoleButtonProps {
  destructive?: boolean
}

interface RowActionButtonProps extends React.ComponentProps<"button"> {
  asChild?: boolean
  destructive?: boolean
}

function PrimaryButton(props: RoleButtonProps) {
  return <Button {...props} />
}

function SecondaryButton({
  className,
  destructive = false,
  ...props
}: SecondaryButtonProps) {
  return (
    <Button
      variant="outline"
      className={cn(
        destructive && "text-destructive hover:text-destructive",
        className
      )}
      {...props}
    />
  )
}

function DestructiveButton(props: RoleButtonProps) {
  return <Button variant="destructive" {...props} />
}

function AppBarIconButton(props: IconRoleButtonProps) {
  return <Button variant="outline" size="icon" {...props} />
}

function IconButton(props: IconRoleButtonProps) {
  return <Button variant="ghost" size="icon" {...props} />
}

function RowActionButton({
  className,
  asChild = false,
  destructive = false,
  ...props
}: RowActionButtonProps) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      type={asChild ? undefined : "button"}
      className={cn(
        "flex w-full items-center gap-3 px-6 py-3 text-left text-sm hover:bg-accent/50 disabled:pointer-events-none disabled:text-muted-foreground [&_svg]:size-4 [&_svg]:shrink-0",
        destructive && "text-destructive",
        className
      )}
      {...props}
    />
  )
}

export {
  PrimaryButton,
  SecondaryButton,
  DestructiveButton,
  AppBarIconButton,
  IconButton,
  RowActionButton,
}
