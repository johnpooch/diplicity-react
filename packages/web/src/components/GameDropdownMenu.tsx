import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Info, Users, Share, MoreHorizontal } from "lucide-react";

interface GameDropdownMenuProps {
  gameId: string;
  onNavigateToGameInfo: () => void;
  onNavigateToPlayerInfo: () => void;
}

export function GameDropdownMenu({
  gameId,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" aria-label="Game menu">
          <MoreHorizontal />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={onNavigateToGameInfo}>
          <Info />
          Game info
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onNavigateToPlayerInfo}>
          <Users />
          Player info
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => {
            navigator.clipboard.writeText(
              `${window.location.origin}/game/${gameId}`
            );
          }}
        >
          <Share />
          Share
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
