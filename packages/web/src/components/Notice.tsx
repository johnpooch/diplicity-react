import React from "react";
import {
  Empty,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from "@/components/ui/empty";
import { type LucideIcon } from "lucide-react";

interface NoticeProps {
  icon?: LucideIcon;
  title: string;
  message?: string | React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}

const Notice: React.FC<NoticeProps> = ({
  icon: Icon,
  title,
  message,
  className,
  actions,
}) => {
  return (
    <Empty className={className}>
      <EmptyHeader>
        {Icon && (
          <EmptyMedia variant="icon">
            <Icon className="opacity-60" />
          </EmptyMedia>
        )}
        <EmptyTitle>{title}</EmptyTitle>
        {message && (
          <EmptyDescription>
            {typeof message === "string" ? message : message}
          </EmptyDescription>
        )}
      </EmptyHeader>
      {actions && <EmptyContent>{actions}</EmptyContent>}
    </Empty>
  );
};

export { Notice };
export type { NoticeProps };
