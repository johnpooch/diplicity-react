import React from "react";
import {
  Empty,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from "@/components/ui/empty";
import { Icon, IconName } from "@/components/Icon";

interface NoticeProps {
  icon?: IconName;
  title: string;
  message?: string | React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}

const Notice: React.FC<NoticeProps> = ({
  icon,
  title,
  message,
  className,
  actions,
}) => {
  return (
    <Empty className={className}>
      <EmptyHeader>
        {icon && (
          <EmptyMedia variant="icon">
            <Icon name={icon} variant="lucide" className="opacity-60" />
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
