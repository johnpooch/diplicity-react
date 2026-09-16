import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { Trash2 } from "lucide-react";
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
  useGameDeleteDestroy,
  getGamesListQueryKey,
} from "@/api/generated/endpoints";

interface DeleteGameActionProps {
  game: {
    id: string;
    sandbox: boolean;
  };
}

export const DeleteGameAction: React.FC<DeleteGameActionProps> = ({
  game,
}) => {
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const deleteGameMutation = useGameDeleteDestroy();

  const handleDeleteGame = async () => {
    setShowDeleteConfirmation(false);
    try {
      await deleteGameMutation.mutateAsync({ gameId: game.id });
      toast.success("Game deleted");
      queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
      navigate("/");
    } catch {
      toast.error("Failed to delete game");
    }
  };

  return (
    <>
      <Button
        size="sm"
        variant="outline"
        className="flex-1"
        onClick={() => setShowDeleteConfirmation(true)}
      >
        <Trash2 />
        Delete game
      </Button>

      <AlertDialog
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {game.sandbox ? "Delete sandbox game" : "Delete game"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {game.sandbox
                ? "This will permanently delete this sandbox game and all its data. This action cannot be undone."
                : "This will permanently delete this game. Players who have joined will be notified. This action cannot be undone."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteGame}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
