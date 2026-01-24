import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Info, Users, Share, MoreHorizontal, LogOut } from "lucide-react";
import {
  useGameLeaveDestroy,
  getGamesListQueryKey,
} from "@/api/generated/endpoints";

interface GameDropdownMenuProps {
  gameId: string;
  canLeave: boolean;
  onNavigateToGameInfo: () => void;
  onNavigateToPlayerInfo: () => void;
}

export function GameDropdownMenu({
  gameId,
  canLeave,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  const queryClient = useQueryClient();
  const leaveGameMutation = useGameLeaveDestroy();

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId });
      toast.success("Successfully left game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to leave game");
    }
  };

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
            toast.success("Link copied to clipboard");
          }}
        >
          <Share />
          Share
        </DropdownMenuItem>
        {canLeave && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLeaveGame}>
              <LogOut />
              Leave game
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
