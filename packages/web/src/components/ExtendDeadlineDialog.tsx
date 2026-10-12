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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DurationEnum } from "@/api/generated/endpoints";
import { EXTEND_DURATION_OPTIONS } from "@/constants";

interface ExtendDeadlineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (duration: DurationEnum) => void;
}

export const ExtendDeadlineDialog: React.FC<ExtendDeadlineDialogProps> = ({
  open,
  onOpenChange,
  onConfirm,
}) => {
  const [selectedDuration, setSelectedDuration] = useState<DurationEnum>(
    DurationEnum["24_hours"]
  );

  const handleOpenChange = (nextOpen: boolean) => {
    onOpenChange(nextOpen);
    if (!nextOpen) {
      setSelectedDuration(DurationEnum["24_hours"]);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
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
          <AlertDialogAction
            onClick={() => {
              onConfirm(selectedDuration);
              handleOpenChange(false);
            }}
          >
            Extend
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
