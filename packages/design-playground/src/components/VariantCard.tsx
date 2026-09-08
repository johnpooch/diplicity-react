import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { StaticMap } from "@/components/StaticMap";
import { cn } from "@/lib/utils";
import { ChevronRight, Trophy } from "lucide-react";
import type { Variant } from "@/data/types";

interface VariantCardProps {
  variant: Variant;
  to: string;
  compact?: boolean;
  className?: string;
}

const VariantCard: React.FC<VariantCardProps> = ({
  variant,
  to,
  compact = false,
  className,
}) => {
  return (
    <Link to={to} className={cn("block", className)}>
      <Card className="overflow-hidden py-0 transition-colors hover:bg-accent/50">
        <CardContent className="p-0">
          <div
            className={cn("flex", compact ? "flex-row" : "flex-col")}
          >
            <div
              className={cn(
                "overflow-hidden",
                compact ? "w-1/3 shrink-0" : "w-full"
              )}
            >
              <StaticMap className="aspect-video w-full object-cover" />
            </div>
            <div className="flex min-w-0 flex-1 items-center gap-3 p-4">
              <div className="flex min-w-0 flex-1 flex-col gap-1">
                <h3 className="truncate font-semibold leading-tight">
                  {variant.name}
                </h3>
                <p className="line-clamp-2 text-sm text-muted-foreground">
                  {variant.description}
                </p>
                <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Trophy className="size-4 shrink-0" />
                  <span className="min-w-0 truncate">
                    {variant.victoryConditions}
                  </span>
                </p>
              </div>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

export { VariantCard };
