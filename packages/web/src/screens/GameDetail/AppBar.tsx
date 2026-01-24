import React from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useIsMobile } from "@/hooks/use-mobile";

interface GameDetailAppBarProps {
  title?: string | React.ReactNode;
  onNavigateBack?: () => void;
  leftButton?: React.ReactNode;
  rightButton?: React.ReactNode;
  variant?: "primary" | "secondary";
}

const GameDetailAppBar: React.FC<GameDetailAppBarProps> = ({
  title,
  onNavigateBack,
  leftButton,
  rightButton,
  variant = "primary",
}) => {
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const handleBack = () => {
    if (onNavigateBack) {
      onNavigateBack();
    } else {
      navigate(-1);
    }
  };

  const showCloseButton = variant === "secondary" && !isMobile;
  const showBackButton = isMobile;

  return (
    <>
      <div
        className={cn(
          "flex items-center justify-between h-14 px-2",
          "bg-background"
        )}
      >
        {/* Left section */}
        <div className="flex items-center gap-2">
          {leftButton ||
            (showBackButton && (
              <Button variant="ghost" size="icon" onClick={handleBack}>
                <ArrowLeft className="size-5" />
              </Button>
            ))}
        </div>

        {/* Center - Title */}
        <div className="flex-1 text-center">
          {typeof title === "string" ? (
            <h1 className="text-lg font-semibold truncate">{title}</h1>
          ) : (
            title
          )}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-2">
          {rightButton ||
            (showCloseButton && (
              <Button variant="ghost" size="icon" onClick={handleBack}>
                <X className="size-5" />
              </Button>
            ))}
        </div>
      </div>
      <Separator />
    </>
  );
};

export { GameDetailAppBar };
