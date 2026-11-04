import React from "react";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";

const sections = [
  {
    title: "What your rating shows",
    body: "Your rating reflects how well you have done against the players you have faced in ranked games. Beat strong opponents and it rises further; lose to weaker ones and it falls further.",
  },
  {
    title: "How a game counts",
    body: "Winners and drawers beat everyone else in the game. The remaining players tie with each other.",
  },
  {
    title: "New ratings",
    body: "A new rating moves faster, so it finds your level quickly. You appear on the leaderboard once your rating has settled.",
  },
  {
    title: "Leaving and taking over",
    body: "Leaving a game counts as a loss. Taking over a vacated seat can only help your rating, never hurt it.",
  },
  {
    title: "Which games are ranked",
    body: "Only public games marked as ranked, on variants that support ranking, count towards your rating.",
  },
];

const HowRatingsWork: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="How ratings work" />
    <div className="space-y-6">
      {sections.map(section => (
        <section key={section.title} className="space-y-1">
          <h2 className="font-semibold">{section.title}</h2>
          <p className="text-sm text-muted-foreground">{section.body}</p>
        </section>
      ))}
    </div>
  </ScreenContainer>
);

const HowRatingsWorkSuspense: React.FC = () => <HowRatingsWork />;

export { HowRatingsWorkSuspense as HowRatingsWork };
