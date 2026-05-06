import React from "react";
import { cn } from "@/lib/utils";

interface InfoPanelProps {
  className?: string;
}

const LEARN_LINK =
  "https://diplicity.notion.site/Diplicity-FAQ-7b4e0a119eb54c69b80b411f14d43bb9";

const InfoPanel: React.FC<InfoPanelProps> = ({ className }) => {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <h2 className="text-base font-semibold">Welcome to Diplicity!</h2>
      <p className="text-sm text-muted-foreground">
        If you're new to the game, read our{" "}
        <a
          href={LEARN_LINK}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          FAQ
        </a>
        .
      </p>
    </div>
  );
};

export { InfoPanel };
export type { InfoPanelProps };
