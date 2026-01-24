import * as React from "react";
import { Portal } from "@radix-ui/react-portal";
import { DismissableLayer } from "@radix-ui/react-dismissable-layer";
import { useIsMobile } from "@/hooks/use-mobile";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

export interface FloatingMenuProps {
  open: boolean;
  x: number;
  y: number;
  container?: Element | null;
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

const getPosition = (x: number, y: number, container?: Element | null) => {
  const menuWidth = 200;
  const menuHeight = 200;

  let left = x;
  let top = y;

  if (container) {
    const rect = container.getBoundingClientRect();
    left = rect.left + x;
    top = rect.top + y;
  }

  // Adjust for right edge
  if (left + menuWidth > window.innerWidth) {
    left = left - menuWidth;
  }

  // Adjust for bottom edge
  if (top + menuHeight > window.innerHeight) {
    top = top - menuHeight;
  }

  // Ensure minimum padding from edges
  left = Math.max(8, left);
  top = Math.max(8, top);

  return { top, left };
};

function FloatingMenu({
  open,
  x,
  y,
  container,
  children,
  onClose,
  className,
}: FloatingMenuProps) {
  const isMobile = useIsMobile();

  if (!open) return null;

  // Mobile: Bottom sheet
  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={open => !open && onClose?.()}>
        <SheetContent side="bottom" className="rounded-t-lg">
          <div role="menu" className="flex flex-col py-1">
            {children}
          </div>
        </SheetContent>
      </Sheet>
    );
  }

  // Desktop: Floating positioned menu
  const position = getPosition(x, y, container);

  return (
    <Portal>
      <DismissableLayer
        onEscapeKeyDown={onClose}
        onPointerDownOutside={onClose}
        onFocusOutside={onClose}
      >
        <div
          role="menu"
          className={cn(
            "bg-popover text-popover-foreground fixed z-50 min-w-[8rem] rounded-md border p-1 shadow-md",
            "animate-in fade-in-0 zoom-in-95",
            className
          )}
          style={{
            top: position.top,
            left: position.left,
          }}
        >
          {children}
        </div>
      </DismissableLayer>
    </Portal>
  );
}

interface FloatingMenuItemProps extends React.ComponentProps<"div"> {
  variant?: "default" | "destructive";
}

function FloatingMenuItem({
  className,
  variant = "default",
  ...props
}: FloatingMenuItemProps) {
  return (
    <div
      role="menuitem"
      data-variant={variant}
      className={cn(
        "relative flex cursor-default select-none items-center gap-2 rounded-sm px-3 py-2 text-sm outline-none",
        "hover:bg-accent hover:text-accent-foreground",
        "focus:bg-accent focus:text-accent-foreground",
        "data-[variant=destructive]:text-destructive data-[variant=destructive]:hover:bg-destructive/10 data-[variant=destructive]:focus:bg-destructive/10",
        "[&_svg:not([class*='text-'])]:text-muted-foreground [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    />
  );
}

function FloatingMenuSeparator({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      role="separator"
      className={cn("bg-border -mx-1 my-1 h-px", className)}
      {...props}
    />
  );
}

export { FloatingMenu, FloatingMenuItem, FloatingMenuSeparator };
