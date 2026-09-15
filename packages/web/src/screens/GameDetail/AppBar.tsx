import React from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, X } from "lucide-react";
import { Button } from "@/components/ui/button";
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
      if (variant === "primary") {
        navigate(`/`);
      } else {
        navigate(-1);
      }
    }
  };

  const showBackButton = variant === "secondary" || isMobile;

  return (
    <div className="flex min-h-14 items-center gap-3 px-2 md:px-3">
      {/* Left section */}
      <div className="flex items-center gap-2">
        {leftButton ||
          (showBackButton &&
            (variant === "primary" ? (
              <Button variant="ghost" size="icon" onClick={handleBack}>
                <X className="size-5" />
              </Button>
            ) : (
              <Button
                variant="outline"
                size="icon-sm"
                className="rounded-full"
                onClick={handleBack}
                aria-label="Back"
              >
                <ArrowLeft />
              </Button>
            )))}
      </div>

      {/* Center - Title */}
      <div className="flex-1 min-w-0">
        {typeof title === "string" ? (
          <h1 className="text-xl font-semibold leading-9 truncate">{title}</h1>
        ) : (
          title
        )}
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2">{rightButton}</div>
    </div>
  );
};

export { GameDetailAppBar };
