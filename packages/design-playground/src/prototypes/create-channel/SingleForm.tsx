import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { createChannelMembers } from "@/data/fixtures";
import type { Player } from "@/data/types";
import { cn } from "@/lib/utils";

const chatListPath = "/chat-channel-list/single-list/active";
const createdChannelPath = "/chat-channel/nation-bubbles/empty";

const displayName = (player: Player) =>
  player.anonymous ? "Anonymous" : player.name;

const roleLabel = (player: Player) => {
  if (player.role === "admin") return "admin";
  if (player.role === "bot") return "bot";
  return undefined;
};

const initials = (player: Player) => displayName(player).charAt(0).toUpperCase();

const MemberRow: React.FC<{
  player: Player;
  selected: boolean;
  onToggle: () => void;
}> = ({ player, selected, onToggle }) => {
  const name = displayName(player);
  const role = roleLabel(player);
  const nation = player.assignedNation ?? player.name;

  return (
    <Card
      className={cn(
        "overflow-hidden py-0 transition-colors hover:bg-accent/50",
        selected && "bg-accent/50"
      )}
    >
      <CardContent className="p-0">
        <label className="flex w-full cursor-pointer items-center gap-3 p-3">
          <div className="relative size-12 shrink-0">
            <div className="size-12 overflow-hidden rounded-full border">
              <NationFlag nation={nation} />
            </div>
            {!player.anonymous && (
              <span className="absolute -bottom-0.5 -right-0.5">
                <Avatar className="size-5 ring-2 ring-card">
                  {player.picture && <AvatarImage src={player.picture} alt="" />}
                  <AvatarFallback className="text-[8px]">
                    {initials(player)}
                  </AvatarFallback>
                </Avatar>
              </span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold leading-tight">{nation}</p>
            <p className="truncate text-sm text-muted-foreground">
              {name}
              {role && ` (${role})`}
            </p>
          </div>
          <Checkbox
            checked={selected}
            onCheckedChange={onToggle}
            aria-label={`Select ${nation}`}
          />
        </label>
      </CardContent>
    </Card>
  );
};

const CreateChannel: React.FC = () => {
  const navigate = useNavigate();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [name, setName] = useState("");

  const toggle = (id: string) => {
    setSelectedIds(current =>
      current.includes(id)
        ? current.filter(item => item !== id)
        : [...current, id]
    );
  };

  return (
    <GameDetailShell
      title="Create channel"
      activeNavItem="Chat"
      mode="secondary"
      backTo={chatListPath}
    >
      <ScreenContainer>
        <section className="flex flex-col gap-2">
          <Label htmlFor="channel-name">Channel name</Label>
          <Input
            id="channel-name"
            value={name}
            onChange={event => setName(event.target.value)}
            placeholder="Optional"
          />
        </section>
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-muted-foreground">Members</h2>
          <div className="flex flex-col gap-2">
            {createChannelMembers.map(player => (
              <MemberRow
                key={player.id}
                player={player}
                selected={selectedIds.includes(player.id)}
                onToggle={() => toggle(player.id)}
              />
            ))}
          </div>
        </section>
        <Button
          className="w-full"
          size="lg"
          disabled={selectedIds.length === 0}
          onClick={() => navigate(createdChannelPath)}
        >
          Create channel
        </Button>
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { CreateChannel };
