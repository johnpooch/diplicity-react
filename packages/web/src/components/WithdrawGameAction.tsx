import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { SecondaryButton } from "@/components/ui/role-buttons";
import { WithdrawDialog } from "@/components/WithdrawDialog";
import {
  useGameMemberWithdrawPartialUpdate,
  getGamesListQueryKey,
  getGameRetrieveQueryKey,
  WithdrawalReasonEnum,
} from "@/api/generated/endpoints";

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

  const handleWithdraw = async (reason: WithdrawalReasonEnum) => {
    try {
      await withdrawMutation.mutateAsync({ gameId: game.id, data: { reason } });
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
      <SecondaryButton
        disabled={withdrawMutation.isPending}
        onClick={() => setShowConfirmation(true)}
      >
        <LogOut />
        Withdraw from game
      </SecondaryButton>

      <WithdrawDialog
        open={showConfirmation}
        onOpenChange={setShowConfirmation}
        isFirstYear={game.isFirstYear}
        onConfirm={handleWithdraw}
      />
    </>
  );
};
