import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckSquare, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  getGameRetrieveQueryKey,
  useGameConfirmPhasePartialUpdate,
} from "@/api/generated/endpoints";
import type { OrderCount } from "@/utils/orderCount";

interface ConfirmOrdersButtonProps {
  gameId: string;
  confirmed: boolean;
  count?: OrderCount | null;
  className?: string;
}

const ConfirmOrdersButton: React.FC<ConfirmOrdersButtonProps> = ({
  gameId,
  confirmed,
  count,
  className,
}) => {
  const queryClient = useQueryClient();
  const confirmOrdersMutation = useGameConfirmPhasePartialUpdate();

  const handleConfirmOrders = async () => {
    const newConfirmedState = !confirmed;
    try {
      await confirmOrdersMutation.mutateAsync({
        gameId,
        data: { ordersConfirmed: newConfirmedState },
      });
      queryClient.invalidateQueries({
        queryKey: getGameRetrieveQueryKey(gameId),
      });
      toast.success(
        newConfirmedState ? "Orders confirmed" : "Orders unconfirmed"
      );
    } catch {
      toast.error(
        newConfirmedState
          ? "Failed to confirm orders"
          : "Failed to unconfirm orders"
      );
    }
  };

  const label = confirmed ? "Confirmed" : "Confirm";

  return (
    <Button
      disabled={confirmOrdersMutation.isPending}
      onClick={handleConfirmOrders}
      className={className}
    >
      {confirmed ? <CheckSquare /> : <Square />}
      {count ? `${label} (${count.submitted}/${count.total})` : label}
    </Button>
  );
};

export { ConfirmOrdersButton };
