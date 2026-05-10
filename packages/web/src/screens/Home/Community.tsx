import React from "react";
import { ExternalLink } from "lucide-react";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { Button } from "@/components/ui/button";

const DISCORD_URL =
  "https://discord.com/channels/565625522407604254/697344626859704340";

const GITHUB_DISCUSSIONS_URL =
  "https://github.com/johnpooch/diplicity-react/discussions";

const DiscordIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    role="img"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="currentColor"
    aria-label="Discord"
  >
    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
  </svg>
);

const GitHubIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    role="img"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="currentColor"
    aria-label="GitHub"
  >
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
  </svg>
);

const Community: React.FC = () => {
  const handleOpenDiscord = () => {
    window.open(DISCORD_URL, "_blank", "noopener,noreferrer");
  };

  const handleOpenDiscussions = () => {
    window.open(GITHUB_DISCUSSIONS_URL, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-4">
      <ScreenCard>
        <ScreenCardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <DiscordIcon className="size-5" />
            <h2 className="text-lg font-semibold">Join the community</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Chat with fellow Diplomacy players, find open games, and jump into
            strategy discussions on our Discord server. Whether you're new to
            the game or a seasoned veteran, there's a place for you — and you
            can chat directly with the developers.
          </p>
          <Button onClick={handleOpenDiscord} className="w-full">
            <ExternalLink className="size-4" />
            Open Discord
          </Button>
        </ScreenCardContent>
      </ScreenCard>

      <ScreenCard>
        <ScreenCardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <GitHubIcon className="size-5" />
            <h2 className="text-lg font-semibold">
              Report bugs &amp; request features
            </h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Diplicity is open source and built by a small team in our spare
            time. Found a bug? Have an idea? Head to GitHub Discussions — every
            report and suggestion genuinely helps. You can also browse the code
            and contribute directly, or with our help.
          </p>
          <Button onClick={handleOpenDiscussions} className="w-full">
            <ExternalLink className="size-4" />
            Open GitHub Discussions
          </Button>
        </ScreenCardContent>
      </ScreenCard>
    </div>
  );
};

const CommunitySuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Community" />
      <Community />
    </ScreenContainer>
  );
};

export { CommunitySuspense as Community };
