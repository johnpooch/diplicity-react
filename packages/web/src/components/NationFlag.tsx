import React from "react";
import { Flags } from "../assets/flags";
import { cn } from "../lib/utils";

interface NationFlagProps {
  nation: string;
  variantId: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "size-4",
  md: "size-5",
  lg: "size-6",
};

const NationFlag: React.FC<NationFlagProps> = ({
  nation,
  variantId,
  size = "md",
  className,
}) => {
  const flag =
    Flags[variantId as keyof typeof Flags]?.[
      nation.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
    ];

  if (!flag) return null;

  return (
    <img
      src={flag}
      alt={nation}
      className={cn("rounded-full object-cover", sizeClasses[size], className)}
    />
  );
};

export { NationFlag };
