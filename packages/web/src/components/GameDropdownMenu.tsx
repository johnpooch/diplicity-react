import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
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
import {
  Info,
  Users,
  Share,
  MoreHorizontal,
  LogOut,
  Trash2,
} from "lucide-react";
import {
  useGameLeaveDestroy,
  useGameDeleteDestroy,
  useGameMemberWithdrawPartialUpdate,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
  GameList,
} from "@/api/generated/endpoints";
import { copyLink } from "@/utils/copyLink";

interface GameDropdownMenuProps {
  game: Pick<
    GameList,
    "id" | "sandbox" | "canLeave" | "canWithdraw" | "canDelete" | "status"
  >;
  onNavigateToGameInfo?: () => void;
  onNavigateToPlayerInfo?: () => void;
}

export function GameDropdownMenu({
  game,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showWithdrawConfirmation, setShowWithdrawConfirmation] =
    useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const leaveGameMutation = useGameLeaveDestroy();
  const deleteGameMutation = useGameDeleteDestroy();
  const withdrawMutation = useGameMemberWithdrawPartialUpdate();

  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Successfully left game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to leave game");
    }
  };

  const handleWithdraw = async () => {
    setShowWithdrawConfirmation(false);
    try {
      await withdrawMutation.mutateAsync({ gameId: game.id });
      toast.success("You have withdrawn from the game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(game.id),
      });
    } catch {
      toast.error("Failed to withdraw from game");
    }
  };

  const handleDeleteGame = async () => {
    setShowDeleteConfirmation(false);
    try {
      await deleteGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Game deleted");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      navigate("/");
    } catch {
      toast.error("Failed to delete game");
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          aria-label="Game menu"
          className="relative"
        >
          <MoreHorizontal />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {onNavigateToGameInfo && (
          <DropdownMenuItem onClick={onNavigateToGameInfo}>
            <Info />
            Game info
          </DropdownMenuItem>
        )}
        {onNavigateToPlayerInfo && (
          <DropdownMenuItem onClick={onNavigateToPlayerInfo}>
            <Users />
            Player info
          </DropdownMenuItem>
        )}
        {(onNavigateToGameInfo || onNavigateToPlayerInfo) && (
          <DropdownMenuSeparator />
        )}
        <DropdownMenuItem onClick={() => copyLink(`/game/${game.id}`)}>
          <Share />
          Share
        </DropdownMenuItem>
        {game.canLeave && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLeaveGame}>
              <LogOut />
              Leave game
            </DropdownMenuItem>
          </>
        )}
        {game.canWithdraw && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowWithdrawConfirmation(true)}>
              <LogOut />
              Withdraw from game
            </DropdownMenuItem>
          </>
        )}
        {game.canDelete && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowDeleteConfirmation(true)}>
              <Trash2 />
              Delete game
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>

      <AlertDialog
        open={showWithdrawConfirmation}
        onOpenChange={setShowWithdrawConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Withdraw from game</AlertDialogTitle>
            <AlertDialogDescription>
              Your seat will be left for another player to claim and you cannot
              rejoin this game. Your commitment rating is not affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleWithdraw}>
              Withdraw
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {game.sandbox ? "Delete sandbox game" : "Delete game"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {game.sandbox
                ? "This will permanently delete this sandbox game and all its data. This action cannot be undone."
                : "This will permanently delete this game. Players who have joined will be notified. This action cannot be undone."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteGame}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DropdownMenu>
  );
}
