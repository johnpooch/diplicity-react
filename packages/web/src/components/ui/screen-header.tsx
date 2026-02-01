import * as React from "react"

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
      <div className="flex items-center gap-2">
        {actions}
        {showUserAvatar && <UserAvatar />}
      </div>
    </div>
  );
}

export { ScreenHeader }
