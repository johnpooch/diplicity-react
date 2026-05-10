import React from "react";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GuideContent } from "@/components/GuideContent";

const LearnToPlay: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="How to Play" />

      <div>
        <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-3">
          Quick-start guide · 5 minute read
        </div>
        <p className="text-[17px] leading-[1.65] text-muted-foreground mb-6">
          Diplomacy looks like a war game. It isn&apos;t — at least not in the
          usual sense. The board is a stage; the real game is the conversation
          around it.
        </p>
      </div>

      <GuideContent />
    </ScreenContainer>
  );
};

const LearnToPlaySuspense: React.FC = () => <LearnToPlay />;

export { LearnToPlaySuspense as LearnToPlay };
