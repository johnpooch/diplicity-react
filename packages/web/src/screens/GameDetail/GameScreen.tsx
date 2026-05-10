import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  Info,
  Users,
  Share,
  Copy,
  Clock,
  Pause,
  Play,
  Vote,
  LogOut,
  Trash2,
  ChevronRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
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
  Item,
  ItemContent,
  ItemTitle,
  ItemGroup,
  ItemSeparator,
  ItemActions,
} from "@/components/ui/item";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { useRequiredParams } from "@/hooks";
import {
  useGameRetrieveSuspense,
  useGameLeaveDestroy,
  useGameDeleteDestroy,
  useGameCloneToSandboxCreate,
  useGameExtendDeadlineUpdate,
  useGamePauseUpdate,
  useGameUnpausePartialUpdate,
  useGamesDrawProposalsListSuspense,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
  getGamePhasesListQueryKey,
  getGamePhaseRetrieveQueryKey,
  DrawProposal,
  DurationEnum,
} from "@/api/generated/endpoints";
import { EXTEND_DURATION_OPTIONS } from "@/constants";

interface DrawProposalBadgeProps {
  gameId: string;
  currentMemberId?: number;
}

const getPendingVotesCount = (
  proposals: DrawProposal[],
  currentMemberId?: number
) => {
  return proposals.filter(p => {
    if (p.status !== "pending") return false;
    const userVote = p.votes.find(v => v.member.id === currentMemberId);
    return userVote && userVote.accepted === null;
  }).length;
};

const DrawProposalBadge: React.FC<DrawProposalBadgeProps> = ({
  gameId,
  currentMemberId,
}) => {
  const { data: proposals } = useGamesDrawProposalsListSuspense(gameId);
  const pendingVotesCount = getPendingVotesCount(proposals, currentMemberId);

  if (pendingVotesCount === 0) return null;

  return (
    <Badge variant="destructive" className="ml-auto h-5 w-5 p-0 justify-center">
      {pendingVotesCount}
    </Badge>
  );
};

const GameScreen: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  const { data: game } = useGameRetrieveSuspense(gameId);

  const [showCloneConfirmation, setShowCloneConfirmation] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showExtendDeadlineDialog, setShowExtendDeadlineDialog] = useState(false);
  const [selectedDuration, setSelectedDuration] = useState<DurationEnum>(
    DurationEnum["24_hours"]
  );

  const leaveGameMutation = useGameLeaveDestroy();
  const deleteGameMutation = useGameDeleteDestroy();
  const cloneToSandboxMutation = useGameCloneToSandboxCreate();
  const extendDeadlineMutation = useGameExtendDeadlineUpdate();
  const pauseGameMutation = useGamePauseUpdate();
  const unpauseGameMutation = useGameUnpausePartialUpdate();

  const currentMember = game.members?.find(m => m.isCurrentUser);
  const isActiveGame = game.status === "active";
  const isCurrentUserGameMaster = currentMember?.isGameMaster ?? false;
  const canExtendDeadline =
    isCurrentUserGameMaster && isActiveGame && !game.isPaused;
  const canPauseGame =
    isCurrentUserGameMaster && isActiveGame && !game.isPaused;
  const canUnpauseGame =
    isCurrentUserGameMaster && isActiveGame && game.isPaused;
  const isActiveOrFinishedGame =
    game.status === "active" ||
    game.status === "completed" ||
    game.status === "abandoned";
  const canViewDrawProposals = !game.sandbox && isActiveOrFinishedGame;

  const handleShare = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}/game/${game.id}`
    );
    toast.success("Link copied to clipboard");
  };

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
      queryClient.invalidateQueries({
        queryKey: getGamePhaseRetrieveQueryKey(game.id, Number(phaseId)),
      });
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
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Game"
        onNavigateBack={() => navigate(-1)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <ItemGroup>
              <Item
                className="cursor-pointer hover:bg-accent/50"
                onClick={() =>
                  navigate(`/game/${gameId}/phase/${phaseId}/game-info`)
                }
              >
                <Info className="size-4 shrink-0" />
                <ItemContent>
                  <ItemTitle>Game info</ItemTitle>
                </ItemContent>
                <ItemActions>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </ItemActions>
              </Item>
              <ItemSeparator />
              <Item
                className="cursor-pointer hover:bg-accent/50"
                onClick={() =>
                  navigate(`/game/${gameId}/phase/${phaseId}/player-info`)
                }
              >
                <Users className="size-4 shrink-0" />
                <ItemContent>
                  <ItemTitle>Player info</ItemTitle>
                </ItemContent>
                <ItemActions>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </ItemActions>
              </Item>
              <ItemSeparator />
              <Item
                className="cursor-pointer hover:bg-accent/50"
                onClick={handleShare}
              >
                <Share className="size-4 shrink-0" />
                <ItemContent>
                  <ItemTitle>Share</ItemTitle>
                </ItemContent>
              </Item>
              {!game.sandbox && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={() => setShowCloneConfirmation(true)}
                  >
                    <Copy className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Clone to sandbox</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
              {canExtendDeadline && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={() => handleExtendDeadlineDialogChange(true)}
                  >
                    <Clock className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Extend deadline</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
              {canPauseGame && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={handlePauseGame}
                  >
                    <Pause className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Pause game</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
              {canUnpauseGame && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={handleUnpauseGame}
                  >
                    <Play className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Resume game</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
              {canViewDrawProposals && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={() =>
                      navigate(`/game/${gameId}/phase/${phaseId}/draw-proposals`)
                    }
                  >
                    <Vote className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Draw proposals</ItemTitle>
                    </ItemContent>
                    <ItemActions>
                      <Suspense fallback={null}>
                        <DrawProposalBadge
                          gameId={game.id}
                          currentMemberId={currentMember?.id}
                        />
                      </Suspense>
                      <ChevronRight className="size-4 text-muted-foreground" />
                    </ItemActions>
                  </Item>
                </>
              )}
              {game.canLeave && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={handleLeaveGame}
                  >
                    <LogOut className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Leave game</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
              {game.canDelete && (
                <>
                  <ItemSeparator />
                  <Item
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={() => setShowDeleteConfirmation(true)}
                  >
                    <Trash2 className="size-4 shrink-0" />
                    <ItemContent>
                      <ItemTitle>Delete game</ItemTitle>
                    </ItemContent>
                  </Item>
                </>
              )}
            </ItemGroup>
          </Panel.Content>
        </Panel>
      </div>

      <AlertDialog
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete sandbox game</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this sandbox game and all its data.
              This action cannot be undone.
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
    </div>
  );
};

const GameScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <GameScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { GameScreenSuspense as GameScreen };
