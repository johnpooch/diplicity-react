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
  Info,
  Users,
  Share,
  MoreHorizontal,
  LogOut,
  Copy,
  Handshake,
  Vote,
} from "lucide-react";
import {
  useGameLeaveDestroy,
  useGameCloneToSandboxCreate,
  getGamesListQueryKey,
  GameList,
  GameRetrieve,
  useGamesDrawProposalsListSuspense,
  DrawProposal,
} from "@/api/generated/endpoints";
import { Suspense } from "react";

interface GameDropdownMenuProps {
  game: Pick<GameList, "id" | "sandbox" | "canLeave"> &
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
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { phaseId } = useParams<{ phaseId: string }>();
  const leaveGameMutation = useGameLeaveDestroy();
  const cloneToSandboxMutation = useGameCloneToSandboxCreate();

  const currentMember = game.members?.find(m => m.isCurrentUser);
  const isActiveGame = game.status === "active";
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
    </DropdownMenu>
  );
}
