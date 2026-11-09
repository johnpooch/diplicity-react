import { useState } from "react";
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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WithdrawalReasonEnum } from "@/api/generated/endpoints";

const WITHDRAWAL_REASONS: Record<WithdrawalReasonEnum, string> = {
  busy: "I'm busy with things outside of Diplomacy",
  too_many_games: "I'm in too many games",
  about_to_be_eliminated: "I'm about to be eliminated",
  losing_position: "I think I'm going to lose",
  dislike_nation: "I don't like my nation",
  not_enjoying: "I'm not enjoying this game",
  other: "Something else",
};

interface WithdrawDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isFirstYear: boolean;
  onConfirm: (reason: WithdrawalReasonEnum) => void;
}

export const WithdrawDialog: React.FC<WithdrawDialogProps> = ({
  open,
  onOpenChange,
  isFirstYear,
  onConfirm,
}) => {
  const [reason, setReason] = useState<WithdrawalReasonEnum | null>(null);

  const handleOpenChange = (nextOpen: boolean) => {
    onOpenChange(nextOpen);
    if (!nextOpen) {
      setReason(null);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Withdraw from game</AlertDialogTitle>
          <AlertDialogDescription>
            {isFirstYear
              ? "Withdrawing in the first year impacts your commitment score negatively. Your seat will be offered to a replacement. You cannot rejoin this game."
              : "Your commitment rating is not affected. You cannot rejoin this game."}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor="withdrawal-reason">Why are you withdrawing?</Label>
          <Select
            value={reason ?? ""}
            onValueChange={value => setReason(value as WithdrawalReasonEnum)}
          >
            <SelectTrigger id="withdrawal-reason" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.values(WithdrawalReasonEnum).map(key => (
                <SelectItem key={key} value={key}>
                  {WITHDRAWAL_REASONS[key]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            disabled={reason === null}
            onClick={() => {
              if (reason === null) return;
              onConfirm(reason);
              handleOpenChange(false);
            }}
          >
            Withdraw
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
