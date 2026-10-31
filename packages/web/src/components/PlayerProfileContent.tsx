import React from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PlayerCommitment } from "@/components/PlayerCommitment";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, children }) => (
  <section className="flex flex-col gap-2">
    <h2 className="text-sm font-medium text-muted-foreground">{title}</h2>
    <Card className="overflow-hidden py-0">
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  </section>
);

interface StatRowProps {
  label: string;
  value: React.ReactNode;
}

const StatRow: React.FC<StatRowProps> = ({ label, value }) => (
  <div className="flex items-center justify-between gap-4 px-6 py-3 text-sm">
    <span>{label}</span>
    <span className="tabular-nums text-muted-foreground">{value}</span>
  </div>
);

interface ProfileCardProps {
  avatar: React.ReactNode;
  name: React.ReactNode;
  joined: React.ReactNode;
}

const ProfileCard: React.FC<ProfileCardProps> = ({ avatar, name, joined }) => (
  <Card className="overflow-hidden py-0">
    <CardContent className="flex items-center gap-4 p-3">
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

export const PlayerProfileContentSkeleton: React.FC = () => (
  <div className="space-y-4">
    <ProfileCard
      avatar={<Skeleton className="size-14 rounded-full" />}
      name={<Skeleton className="my-1 h-5 w-32" />}
      joined={<Skeleton className="mt-2 h-4 w-40" />}
    />
    <Section title="Games">
      <div className="divide-y">
        <StatRow label="Active" value={<Skeleton className="h-5 w-6" />} />
        <StatRow label="Finished" value={<Skeleton className="h-5 w-6" />} />
      </div>
    </Section>
    <PlayerCommitmentSectionSkeleton />
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
          <Avatar className="size-14">
            <AvatarImage src={profile.picture ?? undefined} />
            <AvatarFallback className="text-lg">
              {profile.name[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
        }
        name={
          <h2 className="truncate text-xl font-semibold">{profile.name}</h2>
        }
        joined={
          <p className="text-sm text-muted-foreground">
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
    </div>
  );
};
