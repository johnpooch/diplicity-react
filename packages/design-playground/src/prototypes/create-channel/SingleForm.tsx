import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ListItem, ListSection } from "@/components/ui/list";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDetailShell } from "@/components/GameDetailShell";
import { PlayerMedia } from "@/components/PlayerCard";
import { createChannelMembers } from "@/data/fixtures";
import type { Player } from "@/data/types";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

const chatListPath = "/chat-channel-list/single-list/active";
const createdChannelPath = "/chat-channel/nation-bubbles/empty";

const displayName = (player: Player) =>
  player.anonymous ? "Anonymous" : player.name;

const roleLabel = (player: Player) => {
  if (player.role === "admin") return "admin";
  if (player.role === "bot") return "bot";
  return undefined;
};

const MemberRow: React.FC<{
  player: Player;
  selected: boolean;
  onToggle: () => void;
}> = ({ player, selected, onToggle }) => {
  const name = displayName(player);
  const role = roleLabel(player);
  const nation = player.assignedNation ?? player.name;

  return (
    <ListItem
      className={selected ? "bg-accent/50" : undefined}
      leading={<PlayerMedia player={player} presentation="nation" />}
      title={nation}
      subtitle={role ? `${name} (${role})` : name}
      trailing={
        <span
          aria-hidden
          className={cn(
            "flex size-4 shrink-0 items-center justify-center rounded-[4px] border shadow-xs",
            selected
              ? "border-primary bg-primary text-primary-foreground"
              : "border-input dark:bg-input/30"
          )}
        >
          {selected && <Check className="size-3.5" />}
        </span>
      }
      checked={selected}
      onClick={onToggle}
      ariaLabel={`Select ${nation}`}
    />
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
        <ListSection header="Members">
          {createChannelMembers.map(player => (
            <MemberRow
              key={player.id}
              player={player}
              selected={selectedIds.includes(player.id)}
              onToggle={() => toggle(player.id)}
            />
          ))}
        </ListSection>
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
