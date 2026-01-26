import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Info, Users, Share, MoreHorizontal, LogOut, Copy } from "lucide-react";
import {
  useGameLeaveDestroy,
  useGameCloneToSandboxCreate,
  getGamesListQueryKey,
} from "@/api/generated/endpoints";
import type { GameList } from "@/api/generated/model";

interface GameDropdownMenuProps {
  game: Pick<GameList, "id" | "sandbox" | "canLeave">;
  onNavigateToGameInfo: () => void;
  onNavigateToPlayerInfo: () => void;
}

export function GameDropdownMenu({
  game,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  const [showCloneConfirmation, setShowCloneConfirmation] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const leaveGameMutation = useGameLeaveDestroy();
  const cloneToSandboxMutation = useGameCloneToSandboxCreate();

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Successfully left game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to leave game");
    }
  };

  const handleClone = async () => {
    setShowCloneConfirmation(false);
    try {
      const result = await cloneToSandboxMutation.mutateAsync({
        gameId: game.id,
      });
      toast.success("Sandbox created");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      navigate(`/game/${result.id}`);
    } catch {
      toast.error("Failed to create sandbox");
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
              `${window.location.origin}/game/${game.id}`
            );
            toast.success("Link copied to clipboard");
          }}
        >
          <Share />
          Share
        </DropdownMenuItem>
        {!game.sandbox && (
          <DropdownMenuItem onClick={() => setShowCloneConfirmation(true)}>
            <Copy />
            Clone to sandbox
          </DropdownMenuItem>
        )}
        {game.canLeave && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLeaveGame}>
              <LogOut />
              Leave game
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>

      <AlertDialog
        open={showCloneConfirmation}
        onOpenChange={setShowCloneConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clone to sandbox</AlertDialogTitle>
            <AlertDialogDescription>
              A sandbox copy of this game will be created at the current phase.
              You can use it to explore different strategies. If you already
              have 3 sandbox games, your oldest one will be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleClone}>
              Create sandbox
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DropdownMenu>
  );
}
