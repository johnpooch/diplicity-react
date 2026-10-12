import { useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
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
import { ExtendDeadlineDialog } from "@/components/ExtendDeadlineDialog";
import { ShortGameJoinWarningDialog } from "@/components/ShortGameJoinWarningDialog";
import {
  ACTION_DISPLAY,
  BLOCKED_REASONS,
  confirmationFor,
  type ActionMember,
} from "@/components/actionDisplay";
import {
  useGameExtendDeadlineUpdate,
  useGameKickDestroy,
  useGameLeaveDestroy,
  useGameMemberJoinCreate,
  useGameMemberWithdrawPartialUpdate,
  useGameMusterCreate,
  useGamePauseUpdate,
  useGameRetrieveSuspense,
  useGameUnpausePartialUpdate,
  getGameAddableUserListQueryKey,
  getGameMemberRetrieveQueryKey,
  getGamePhaseRetrieveQueryKey,
  getGamePhasesListQueryKey,
  getGameRetrieveQueryKey,
  getGamesListQueryKey,
  BlockedReasonEnum,
  DurationEnum,
  MemberActionKeyEnum,
} from "@/api/generated/endpoints";
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";
import { copyLink } from "@/utils/copyLink";

interface ActionListProps {
  gameId: string;
  actions: readonly {
    key: MemberActionKeyEnum;
    blockedReason: BlockedReasonEnum | null;
  }[];
  member?: ActionMember;
  onMemberGone?: () => void;
}

export const ActionList: React.FC<ActionListProps> = ({
  gameId,
  actions,
  member,
  onMemberGone,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { phaseId } = useParams<{ phaseId: string }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const checkNotificationPermission = useCheckNotificationPermission();
  const [openDialog, setOpenDialog] = useState<MemberActionKeyEnum | null>(null);
  const [runningKey, setRunningKey] = useState<MemberActionKeyEnum | null>(null);

  const joinMutation = useGameMemberJoinCreate();
  const musterMutation = useGameMusterCreate();
  const leaveMutation = useGameLeaveDestroy();
  const withdrawMutation = useGameMemberWithdrawPartialUpdate();
  const pauseMutation = useGamePauseUpdate();
  const unpauseMutation = useGameUnpausePartialUpdate();
  const extendDeadlineMutation = useGameExtendDeadlineUpdate();
  const kickMutation = useGameKickDestroy();

  const memberGone = (key: MemberActionKeyEnum) =>
    key === "leave" || key === "remove_from_lobby";

  const mutate = (key: MemberActionKeyEnum, duration: DurationEnum) => {
    switch (key) {
      case "join":
        return joinMutation.mutateAsync({ gameId });
      case "confirm_seat":
        return musterMutation.mutateAsync({ gameId });
      case "leave":
        return leaveMutation.mutateAsync({ gameId });
      case "withdraw":
        return withdrawMutation.mutateAsync({ gameId });
      case "pause":
        return pauseMutation.mutateAsync({ gameId });
      case "unpause":
        return unpauseMutation.mutateAsync({ gameId });
      case "extend_deadline":
        return extendDeadlineMutation.mutateAsync({ gameId, data: { duration } });
      case "remove_from_lobby":
      case "remove_from_game":
        return member && kickMutation.mutateAsync({ gameId, memberId: member.id });
    }
  };

  const invalidate = (key: MemberActionKeyEnum) => {
    const queryKeys: readonly unknown[][] = [
      [...getGameRetrieveQueryKey(gameId)],
      [...getGamesListQueryKey()],
      ...(member && !memberGone(key)
        ? [[...getGameMemberRetrieveQueryKey(gameId, member.id)]]
        : []),
      ...(key === "extend_deadline"
        ? [
            [...getGamePhasesListQueryKey(gameId)],
            ...(phaseId
              ? [[...getGamePhaseRetrieveQueryKey(gameId, Number(phaseId))]]
              : []),
          ]
        : []),
      ...(key === "remove_from_lobby"
        ? [[...getGameAddableUserListQueryKey(gameId)]]
        : []),
    ];
    return Promise.all(
      queryKeys.map(queryKey => queryClient.invalidateQueries({ queryKey }))
    );
  };

  const runMutation = async (
    key: MemberActionKeyEnum,
    duration: DurationEnum = DurationEnum["24_hours"]
  ) => {
    setOpenDialog(null);
    setRunningKey(key);
    const display = ACTION_DISPLAY[key];
    try {
      await mutate(key, duration);
      if (key === "join" && !game.sandbox) checkNotificationPermission();
      if (memberGone(key)) onMemberGone?.();
      await invalidate(key);
      if (display.success) toast.success(display.success(member));
    } catch {
      toast.error(display.error);
    } finally {
      setRunningKey(null);
    }
  };

  const handleClick = (key: MemberActionKeyEnum) => {
    const replacePath = member && `/game/${gameId}/replace/${member.id}`;
    if (key === "edit_nation_preferences") navigate(`/nation-preference/${gameId}`);
    else if (key === "assign_nations") navigate(`/nation-assignment/${gameId}`);
    else if (key === "take_over" && replacePath) navigate(replacePath);
    else if (key === "share_replacement_link" && replacePath) copyLink(replacePath);
    else if (key === "extend_deadline") setOpenDialog(key);
    else if (key === "join" && game.showShortGameJoinWarning) setOpenDialog(key);
    else if (confirmationFor(key, member)) setOpenDialog(key);
    else runMutation(key);
  };

  const confirmation = openDialog ? confirmationFor(openDialog, member) : null;
  const closeDialog = (open: boolean) => !open && setOpenDialog(null);

  return (
    <div className="flex flex-col gap-3">
      {actions.map(action => {
        const display = ACTION_DISPLAY[action.key];
        return (
          <div key={action.key} className="flex flex-col gap-1">
            <Button
              variant={display.primary ? "default" : "outline"}
              disabled={action.blockedReason !== null || runningKey !== null}
              onClick={() => handleClick(action.key)}
            >
              <display.icon />
              {display.label}
            </Button>
            {action.blockedReason && (
              <p className="text-sm text-muted-foreground">
                {BLOCKED_REASONS[action.blockedReason]}
              </p>
            )}
          </div>
        );
      })}

      <AlertDialog open={confirmation !== null} onOpenChange={closeDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmation?.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmation?.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => openDialog && runMutation(openDialog)}
            >
              {confirmation?.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ExtendDeadlineDialog
        open={openDialog === "extend_deadline"}
        onOpenChange={closeDialog}
        onConfirm={duration => runMutation("extend_deadline", duration)}
      />

      <ShortGameJoinWarningDialog
        open={openDialog === "join"}
        onOpenChange={closeDialog}
        onConfirm={() => runMutation("join")}
      />
    </div>
  );
};
