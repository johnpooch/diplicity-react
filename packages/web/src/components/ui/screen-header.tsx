import * as React from "react"

interface ScreenHeaderProps {
  title: string;
  actions?: React.ReactNode;
}

function ScreenHeader({ title, actions }: ScreenHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h1 className="text-2xl font-bold">{title}</h1>
      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  );
}

export { ScreenHeader }
