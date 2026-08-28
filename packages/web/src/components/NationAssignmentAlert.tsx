import React from "react";
import { Flag } from "lucide-react";
import { useNavigate } from "react-router";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface NationAssignmentAlertProps {
  gameId: string;
}

export const NationAssignmentAlert: React.FC<NationAssignmentAlertProps> = ({
  gameId,
}) => {
  const navigate = useNavigate();

  return (
    <Alert>
      <Flag className="size-4" />
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <AlertDescription>
          You can assign nations to players before the game starts.
        </AlertDescription>
        <div className="shrink-0 w-full sm:w-auto">
          <Button
            variant="outline"
            className="w-full sm:w-auto"
            onClick={() => navigate(`/nation-assignment/${gameId}`)}
          >
            Assign nations
          </Button>
        </div>
      </div>
    </Alert>
  );
};
