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
import { Badge } from "@/components/ui/badge";
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
  Handshake,
  Vote,
  Clock,
} from "lucide-react";
import {
  useGameLeaveDestroy,
  useGameCloneToSandboxCreate,
  useGameExtendDeadlineUpdate,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
  GameList,
  GameRetrieve,
  useGamesDrawProposalsListSuspense,
  DrawProposal,
  DurationEnum,
} from "@/api/generated/endpoints";
import { Suspense } from "react";

const DURATION_OPTIONS = [
  { value: DurationEnum["1_hour"], label: "1 hour" },
  { value: DurationEnum["12_hours"], label: "12 hours" },
  { value: DurationEnum["24_hours"], label: "24 hours" },
  { value: DurationEnum["48_hours"], label: "48 hours" },
  { value: DurationEnum["3_days"], label: "3 days" },
  { value: DurationEnum["4_days"], label: "4 days" },
  { value: DurationEnum["1_week"], label: "1 week" },
  { value: DurationEnum["2_weeks"], label: "2 weeks" },
] as const;

interface GameDropdownMenuProps {
  game: Pick<GameList, "id" | "sandbox" | "canLeave" | "isPaused"> &
    Partial<Pick<GameRetrieve, "status" | "members">>;
  onNavigateToGameInfo: () => void;
  onNavigateToPlayerInfo: () => void;
}

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

const DrawProposalTriggerBadge: React.FC<DrawProposalBadgeProps> = ({
  gameId,
  currentMemberId,
}) => {
  const { data: proposals } = useGamesDrawProposalsListSuspense(gameId);
  const pendingVotesCount = getPendingVotesCount(proposals, currentMemberId);

  if (pendingVotesCount === 0) return null;

  return (
    <Badge
      variant="destructive"
      className="absolute -top-1 -right-1 h-4 w-4 p-0 justify-center text-[10px]"
    >
      {pendingVotesCount}
    </Badge>
  );
};

export function GameDropdownMenu({
  game,
  onNavigateToGameInfo,
  onNavigateToPlayerInfo,
}: GameDropdownMenuProps) {
  const [showCloneConfirmation, setShowCloneConfirmation] = useState(false);
  const [showExtendDeadlineDialog, setShowExtendDeadlineDialog] =
    useState(false);
  const [selectedDuration, setSelectedDuration] = useState<DurationEnum>(
    DurationEnum["24_hours"]
  );
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { phaseId } = useParams<{ phaseId: string }>();
  const leaveGameMutation = useGameLeaveDestroy();
  const cloneToSandboxMutation = useGameCloneToSandboxCreate();
  const extendDeadlineMutation = useGameExtendDeadlineUpdate();

  const currentMember = game.members?.find(m => m.isCurrentUser);
  const isActiveGame = game.status === "active";
  const isCurrentUserGameMaster = currentMember?.isGameMaster ?? false;
  const canExtendDeadline =
    isCurrentUserGameMaster && isActiveGame && !game.isPaused;
  const isActiveOrFinishedGame =
    game.status === "active" ||
    game.status === "completed" ||
    game.status === "abandoned";
  const canProposeDraw = !game.sandbox && isActiveGame;
  const canViewDrawProposals = !game.sandbox && isActiveOrFinishedGame;

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
        data: {},
      });
      toast.success("Sandbox created");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      navigate(`/game/${result.id}`);
    } catch {
      toast.error("Failed to create sandbox");
    }
  };

  const handleNavigateToProposeDraw = () => {
    navigate(`/game/${game.id}/phase/${phaseId}/propose-draw`);
  };

  const handleNavigateToDrawProposals = () => {
    navigate(`/game/${game.id}/phase/${phaseId}/draw-proposals`);
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
    } catch {
      toast.error("Failed to extend deadline");
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" aria-label="Game menu" className="relative">
          <MoreHorizontal />
          {canViewDrawProposals && phaseId && (
            <Suspense fallback={null}>
              <DrawProposalTriggerBadge
                gameId={game.id}
                currentMemberId={currentMember?.id}
              />
            </Suspense>
          )}
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
        {canProposeDraw && phaseId && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleNavigateToProposeDraw}>
              <Handshake />
              Propose draw
            </DropdownMenuItem>
          </>
        )}
        {canViewDrawProposals && phaseId && (
          <>
            {!canProposeDraw && <DropdownMenuSeparator />}
            <DropdownMenuItem onClick={handleNavigateToDrawProposals}>
              <Vote />
              Draw proposals
              <Suspense fallback={null}>
                <DrawProposalBadge
                  gameId={game.id}
                  currentMemberId={currentMember?.id}
                />
              </Suspense>
            </DropdownMenuItem>
          </>
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

      <AlertDialog
        open={showExtendDeadlineDialog}
        onOpenChange={handleExtendDeadlineDialogChange}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Extend deadline</AlertDialogTitle>
            <AlertDialogDescription>
              Select how long to extend the current phase deadline.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Select
            value={selectedDuration}
            onValueChange={value => setSelectedDuration(value as DurationEnum)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DURATION_OPTIONS.map(option => (
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
