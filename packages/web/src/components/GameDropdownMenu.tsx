import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Info,
  Users,
  Share,
  MoreHorizontal,
  LogOut,
  Copy,
  Clock,
  Pause,
  Play,
  Trash2,
} from "lucide-react";
import {
  useGameLeaveDestroy,
  useGameDeleteDestroy,
  useGameCloneToSandboxCreate,
  useGameExtendDeadlineUpdate,
  useGamePauseUpdate,
  useGameUnpausePartialUpdate,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
  GameList,
  GameRetrieve,
  DurationEnum,
  getGamePhasesListQueryKey,
  getGamePhaseRetrieveQueryKey,
} from "@/api/generated/endpoints";
import { EXTEND_DURATION_OPTIONS } from "@/constants";

interface GameDropdownMenuProps {
  game: Pick<
    GameList,
    "id" | "sandbox" | "canLeave" | "canDelete" | "canManage" | "isPaused"
  > &
    Partial<Pick<GameRetrieve, "status">>;
  onNavigateToGameInfo: () => void;
  onNavigateToPlayerInfo: () => void;
}

export function GameDropdownMenu({
  game,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  const [showCloneConfirmation, setShowCloneConfirmation] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showExtendDeadlineDialog, setShowExtendDeadlineDialog] =
    useState(false);
  const [selectedDuration, setSelectedDuration] = useState<DurationEnum>(
    DurationEnum["24_hours"]
  );
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { phaseId } = useParams<{ phaseId: string }>();
  const leaveGameMutation = useGameLeaveDestroy();
  const deleteGameMutation = useGameDeleteDestroy();
  const cloneToSandboxMutation = useGameCloneToSandboxCreate();
  const extendDeadlineMutation = useGameExtendDeadlineUpdate();
  const pauseGameMutation = useGamePauseUpdate();
  const unpauseGameMutation = useGameUnpausePartialUpdate();

  const isActiveGame = game.status === "active";
  const canExtendDeadline = game.canManage && isActiveGame && !game.isPaused;
  const canPauseGame = game.canManage && isActiveGame && !game.isPaused;
  const canUnpauseGame = game.canManage && isActiveGame && game.isPaused;
  const handleLeaveGame = async () => {
    try {
      await leaveGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Successfully left game");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to leave game");
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

  const handleClone = async () => {
    setShowCloneConfirmation(false);
    try {
      const result = await cloneToSandboxMutation.mutateAsync({
        gameId: game.id,
        data: {},
      });
      toast.success("Sandbox created");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      navigate(`/game/${result.id}`);
    } catch {
      toast.error("Failed to create sandbox");
    }
  };

  const handleExtendDeadlineDialogChange = (open: boolean) => {
    setShowExtendDeadlineDialog(open);
    if (!open) {
      setSelectedDuration(DurationEnum["24_hours"]);
    }
  };

  const handleExtendDeadline = async () => {
    setShowExtendDeadlineDialog(false);
    try {
      await extendDeadlineMutation.mutateAsync({
        gameId: game.id,
        data: { duration: selectedDuration },
      });
      toast.success("Deadline extended");
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(game.id),
      });
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      queryClient.invalidateQueries({
        queryKey: getGamePhasesListQueryKey(game.id),
      });
      if (phaseId !== undefined) {
        queryClient.invalidateQueries({
          queryKey: getGamePhaseRetrieveQueryKey(game.id, Number(phaseId)),
        });
      }
    } catch {
      toast.error("Failed to extend deadline");
    }
  };

  const handlePauseGame = async () => {
    try {
      await pauseGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Game paused");
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(game.id),
      });
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to pause game");
    }
  };

  const handleUnpauseGame = async () => {
    try {
      await unpauseGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Game resumed");
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(game.id),
      });
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
    } catch {
      toast.error("Failed to resume game");
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
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(
                `https://diplicity.com/game/${game.id}`
              );
              toast.success("Link copied to clipboard");
            } catch {
              toast.error("Failed to copy link");
            }
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
        {canExtendDeadline && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => handleExtendDeadlineDialogChange(true)}
            >
              <Clock />
              Extend deadline
            </DropdownMenuItem>
          </>
        )}
        {canPauseGame && (
          <DropdownMenuItem onClick={handlePauseGame}>
            <Pause />
            Pause game
          </DropdownMenuItem>
        )}
        {canUnpauseGame && (
          <DropdownMenuItem onClick={handleUnpauseGame}>
            <Play />
            Resume game
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

      <AlertDialog
        open={showExtendDeadlineDialog}
        onOpenChange={handleExtendDeadlineDialogChange}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Extend deadline</AlertDialogTitle>
            <AlertDialogDescription className="text-left">
              Select how long to extend the current phase deadline.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Select
            value={selectedDuration}
            onValueChange={value => setSelectedDuration(value as DurationEnum)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {EXTEND_DURATION_OPTIONS.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleExtendDeadline}>
              Extend
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DropdownMenu>
  );
}
