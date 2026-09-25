import React from "react";
import { ExpandableMapPreview } from "@/components/ExpandableMapPreview";
import { useGameVariant } from "@/hooks/useGameVariant";
import type { GameRetrieve } from "@/api/generated/endpoints";

interface PendingGameMapPreviewProps {
  game: GameRetrieve;
}

const PendingGameMapPreview: React.FC<PendingGameMapPreviewProps> = ({
  game,
}) => {
  const variant = useGameVariant(game);
  if (!variant) return null;

  return (
    <ExpandableMapPreview
      variant={variant}
      phase={variant.templatePhase}
      style={{ width: "100%", height: "100%" }}
    />
  );
};

export { PendingGameMapPreview };
