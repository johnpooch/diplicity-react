import * as React from "react"
import { Link } from "react-router"
import { CircleHelp } from "lucide-react"

import { UserAvatar } from "@/components/UserAvatar"

interface ScreenHeaderProps {
  title: string;
  actions?: React.ReactNode;
  showUserAvatar?: boolean;
}

function ScreenHeader({ title, actions, showUserAvatar }: ScreenHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h1 className="text-2xl font-bold">{title}</h1>
      <div className="flex items-center gap-6">
        {actions}
        {showUserAvatar && (
          <Link
            to="/learn-to-play"
            className="md:hidden flex items-center justify-center size-8 text-foreground hover:text-foreground transition-colors"
            aria-label="Learn how to play"
          >
            <CircleHelp className="size-5" />
          </Link>
        )}
        {showUserAvatar && <UserAvatar />}
      </div>
    </div>
  );
}

export { ScreenHeader }
