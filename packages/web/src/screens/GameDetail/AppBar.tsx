import React, { useRef, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
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
  const [isTitleOpen, setIsTitleOpen] = useState(false);
  const titleRef = useRef<HTMLHeadingElement>(null);

  const handleTitleOpenChange = (open: boolean) => {
    const isTruncated = titleRef.current
      ? titleRef.current.scrollWidth > titleRef.current.clientWidth
      : false;
    setIsTitleOpen(open && isTruncated);
  };

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

  const leftContent =
    leftButton ||
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
      )));

  return (
    <div className="flex min-h-12 items-center gap-3 px-2 md:min-h-14 md:px-3">
      {/* Left section */}
      {leftContent && (
        <div className="flex items-center gap-2">{leftContent}</div>
      )}

      {/* Center - Title */}
      <div className="flex-1 min-w-0">
        {typeof title === "string" ? (
          <Tooltip open={isTitleOpen} onOpenChange={handleTitleOpenChange}>
            <TooltipTrigger asChild>
              <h1
                ref={titleRef}
                className="w-full truncate text-left text-base font-semibold leading-7 md:text-xl md:leading-9"
                onClick={() => handleTitleOpenChange(true)}
              >
                {title}
              </h1>
            </TooltipTrigger>
            <TooltipContent side="bottom">{title}</TooltipContent>
          </Tooltip>
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
