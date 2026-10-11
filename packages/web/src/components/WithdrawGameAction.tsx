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

interface WithdrawGameActionProps {
  game: {
    id: string;
  };
}

export const WithdrawGameAction: React.FC<WithdrawGameActionProps> = ({
  game,
}) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const queryClient = useQueryClient();
  const withdrawMutation = useGameMemberWithdrawPartialUpdate();

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
    </>
  );
};
