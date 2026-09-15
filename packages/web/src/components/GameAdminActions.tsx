import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router";
import { toast } from "sonner";
import { Clock, Pause, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
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
  useGameExtendDeadlineUpdate,
  useGamePauseUpdate,
  useGameUnpausePartialUpdate,
  getGameRetrieveQueryKey,
  getGamesListQueryKey,
  getGamePhasesListQueryKey,
  getGamePhaseRetrieveQueryKey,
  DurationEnum,
} from "@/api/generated/endpoints";
import { EXTEND_DURATION_OPTIONS } from "@/constants";

interface GameAdminActionsProps {
  game: {
    id: string;
    isPaused: boolean;
  };
}

export const GameAdminActions: React.FC<GameAdminActionsProps> = ({ game }) => {
  const [showExtendDeadlineDialog, setShowExtendDeadlineDialog] = useState(false);
  const [selectedDuration, setSelectedDuration] = useState<DurationEnum>(
    DurationEnum["24_hours"]
  );
  const queryClient = useQueryClient();
  const { phaseId } = useParams<{ phaseId: string }>();
  const extendDeadlineMutation = useGameExtendDeadlineUpdate();
  const pauseGameMutation = useGamePauseUpdate();
  const unpauseGameMutation = useGameUnpausePartialUpdate();

  const invalidateGame = () => {
    queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(game.id) });
    queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
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
      invalidateGame();
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
      invalidateGame();
    } catch {
      toast.error("Failed to pause game");
    }
  };

  const handleUnpauseGame = async () => {
    try {
      await unpauseGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Game resumed");
      invalidateGame();
    } catch {
      toast.error("Failed to resume game");
    }
  };

  if (game.isPaused) {
    return (
      <div className="flex w-full flex-wrap items-center gap-3 sm:w-auto">
        <Button
          size="sm"
          onClick={handleUnpauseGame}
          disabled={unpauseGameMutation.isPending}
        >
          <Play />
          Resume
        </Button>
        <span className="flex items-center gap-1 text-sm font-medium text-destructive">
          <Pause className="size-4" />
          Paused
        </span>
      </div>
    );
  }

  return (
    <>
      <div className="flex w-full flex-wrap gap-2 sm:w-auto">
        <Button
          size="sm"
          variant="outline"
          onClick={handlePauseGame}
          disabled={pauseGameMutation.isPending}
          className="flex-1 sm:flex-none"
        >
          <Pause />
          Pause
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => handleExtendDeadlineDialogChange(true)}
          className="flex-1 sm:flex-none"
        >
          <Clock />
          Extend deadline
        </Button>
      </div>

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
    </>
  );
};
