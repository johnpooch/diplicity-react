import React from "react";
import { useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GuideContent } from "@/components/GuideContent";

const LearnToPlay: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="w-full">
      <div className="px-6">
        <div className="flex items-center gap-3 mb-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft className="size-5" />
          </Button>
          <h1 className="text-2xl font-bold">How to Play</h1>
        </div>

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
    </div>
  );
};

const LearnToPlaySuspense: React.FC = () => <LearnToPlay />;

export { LearnToPlaySuspense as LearnToPlay };
