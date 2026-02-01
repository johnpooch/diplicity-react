import React from "react";
import { ExternalLink, MessageCircle } from "lucide-react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { Button } from "@/components/ui/button";

const GITHUB_DISCUSSIONS_URL =
  "https://github.com/johnpooch/diplicity-react/discussions";

const Community: React.FC = () => {
  const handleOpenDiscussions = () => {
    window.open(GITHUB_DISCUSSIONS_URL, "_blank", "noopener,noreferrer");
  };

  return (
    <ScreenCard>
      <ScreenCardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <MessageCircle className="size-5" />
          <h2 className="text-lg font-semibold">GitHub Discussions</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Join the conversation! Ask questions, share strategies, report bugs,
          and connect with other Diplicity players.
        </p>
        <Button onClick={handleOpenDiscussions} className="w-full">
          <ExternalLink className="size-4" />
          Open Discussions
        </Button>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const CommunitySuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Community" showUserAvatar />
      <Community />
    </ScreenContainer>
  );
};

export { CommunitySuspense as Community };
