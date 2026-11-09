import React from "react";
import { Link } from "react-router";
import { ChevronRight } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RowActionButton } from "@/components/ui/role-buttons";
import { PlayerCommitment } from "@/components/PlayerCommitment";
import { Section, StatRow } from "@/components/Section";
import {
  useUsersRetrieveSuspense,
  type ReasonEnum,
} from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

interface ProfileCardProps {
  avatar: React.ReactNode;
  name: React.ReactNode;
  joined: React.ReactNode;
}

const ProfileCard: React.FC<ProfileCardProps> = ({ avatar, name, joined }) => (
  <Card className="overflow-hidden py-0">
    <CardContent className="flex items-center gap-3 p-3">
      {avatar}
      <div className="min-w-0 flex-1">
        {name}
        {joined}
      </div>
    </CardContent>
  </Card>
);

export const PlayerCommitmentSectionSkeleton: React.FC = () => (
  <Section title="Commitment">
    <Skeleton className="m-6 h-64" />
  </Section>
);

export const PlayerCommitmentSection: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);

  return (
    <Section title="Commitment">
      <PlayerCommitment
        total={profile.commitmentTotal}
        squares={profile.commitmentSquares}
      />
    </Section>
  );
};

const PlayerRatingSectionSkeleton: React.FC = () => (
  <Section title="Rating">
    <Skeleton className="mx-6 my-3 h-5" />
  </Section>
);

const PlayerRatingSection: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);
  const { rating } = profile;

  return (
    <Section title="Rating">
      {rating === null ? (
        <p className="px-6 py-3 text-sm">No ranked games yet</p>
      ) : (
        <div className="divide-y">
          <StatRow label="Rating" value={rating.rating.toLocaleString("en-US")} />
          {rating.rank === null ? (
            <StatRow label="Leaderboard" value="Not ranked yet" />
          ) : (
            <RowActionButton asChild>
              <Link to="/leaderboard">
                <span className="flex-1">Leaderboard</span>
                <span className="tabular-nums text-muted-foreground">
                  #{rating.rank}
                </span>
                <ChevronRight className="text-muted-foreground" />
              </Link>
            </RowActionButton>
          )}
          <StatRow label="Won" value={rating.won} />
          <StatRow label="Drew" value={rating.drew} />
          <StatRow label="Lost" value={rating.lost} />
          <RowActionButton asChild>
            <Link to="/how-ratings-work">
              <span className="flex-1">How ratings work</span>
              <ChevronRight className="text-muted-foreground" />
            </Link>
          </RowActionButton>
        </div>
      )}
    </Section>
  );
};

const markLabel: Record<ReasonEnum, string> = {
  abuse_and_harassment: "Abuse and harassment",
  multiple_accounts: "Multiple accounts",
  secret_teaming: "Secret teaming",
  abuse_of_admin_powers: "Abuse of admin powers",
  other: "Other conduct violation",
};

export const PlayerConductSectionSkeleton: React.FC = () => (
  <Section title="Conduct history">
    <Skeleton className="mx-6 my-3 h-5" />
  </Section>
);

export const PlayerConductSection: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);

  return (
    <Section title="Conduct history">
      {profile.marks.length === 0 ? (
        <p className="px-6 py-3 text-sm">No bad conduct</p>
      ) : (
        <div className="divide-y">
          {profile.marks.map(mark => (
            <StatRow
              key={`${mark.reason}-${mark.createdAt}`}
              label={markLabel[mark.reason]}
              value={new Date(mark.createdAt).toLocaleDateString(undefined, {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            />
          ))}
        </div>
      )}
    </Section>
  );
};

export const PlayerProfileContentSkeleton: React.FC = () => (
  <div className="space-y-4">
    <ProfileCard
      avatar={<Skeleton className="size-12 rounded-full" />}
      name={<Skeleton className="my-0.5 h-5 w-32" />}
      joined={<Skeleton className="my-0.5 h-4 w-40" />}
    />
    <Section title="Games">
      <div className="divide-y">
        <StatRow label="Active" value={<Skeleton className="h-5 w-6" />} />
        <StatRow label="Finished" value={<Skeleton className="h-5 w-6" />} />
      </div>
    </Section>
    <PlayerCommitmentSectionSkeleton />
    <PlayerRatingSectionSkeleton />
    <PlayerConductSectionSkeleton />
  </div>
);

export const PlayerProfileContent: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);

  return (
    <div className="space-y-4">
      <ProfileCard
        avatar={
          <Avatar className="size-12">
            <AvatarImage src={profile.picture ?? undefined} />
            <AvatarFallback>
              {profile.name[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
        }
        name={
          <h2 className="font-medium truncate">{profile.name}</h2>
        }
        joined={
          <p className="text-sm text-muted-foreground truncate">
            Joined{" "}
            {new Date(profile.createdAt).toLocaleDateString(undefined, {
              year: "numeric",
              month: "long",
            })}
          </p>
        }
      />

      <Section title="Games">
        <div className="divide-y">
          <StatRow label="Active" value={profile.activeGames} />
          <StatRow label="Finished" value={profile.totalGames} />
        </div>
      </Section>

      <PlayerCommitmentSection userId={userId} />
      <PlayerRatingSection userId={userId} />
      <PlayerConductSection userId={userId} />
    </div>
  );
};
