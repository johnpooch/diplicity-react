import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
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
  useGameMemberWithdrawPartialUpdate,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
} from "@/api/generated/endpoints";

export const withdrawConfirmation = (isFirstYear: boolean) => ({
  title: "Withdraw from game",
  description: isFirstYear
    ? "Withdrawing in the first year impacts your commitment score negatively. Your seat will be offered to a replacement. You cannot rejoin this game."
    : "Your commitment rating is not affected. You cannot rejoin this game.",
  confirmLabel: "Withdraw",
});

interface WithdrawGameActionProps {
  game: {
    id: string;
    isFirstYear: boolean;
  };
}

export const WithdrawGameAction: React.FC<WithdrawGameActionProps> = ({
  game,
}) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const queryClient = useQueryClient();
  const withdrawMutation = useGameMemberWithdrawPartialUpdate();
  const confirmation = withdrawConfirmation(game.isFirstYear);

  const handleWithdraw = async () => {
    setShowConfirmation(false);
    try {
      await withdrawMutation.mutateAsync({ gameId: game.id });
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(game.id),
      });
    } catch {
      toast.error("Failed to withdraw from game");
    }
  };

  return (
    <>
      <Button
        variant="outline"
        disabled={withdrawMutation.isPending}
        onClick={() => setShowConfirmation(true)}
      >
        <LogOut />
        Withdraw from game
      </Button>

      <AlertDialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmation.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmation.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleWithdraw}>
              {confirmation.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
