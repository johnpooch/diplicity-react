import { Fab, Stack, Typography } from "@mui/material";
import {
  CheckBox as OrdersConfirmedIcon,
  CheckBoxOutlineBlank as ConfirmOrdersIcon,
} from "@mui/icons-material";
import {
  mergeQueries,
  useGetUserNewestPhaseStateQuery,
  useUpdatePhaseStateMutation,
} from "../../common";
import { useGameDetailContext } from "../../context";

const useConfirmOrdersAction = () => {
  const { gameId } = useGameDetailContext();
  const phaseStateQuery = useGetUserNewestPhaseStateQuery(gameId);
  const [updatePhaseStateTrigger, updatePhaseStateMutation] =
    useUpdatePhaseStateMutation(gameId);

  const handleClick = () =>
    updatePhaseStateTrigger({
      isConfirmed: !phaseStateQuery.data?.ReadyToResolve,
    });

  const mergedQuery = mergeQueries([phaseStateQuery], (phaseState) => ({
    isConfirmed: Boolean(phaseState?.ReadyToResolve),
    canUpdate: Boolean(phaseState?.canUpdate),
  }));

  return {
    ...mergedQuery,
    isSubmitting: updatePhaseStateMutation.isLoading,
    handleClick,
  };
};

const ConfirmOrdersAction: React.FC = () => {
  const { isLoading, isError, isSuccess, isSubmitting, data, handleClick } =
    useConfirmOrdersAction();

  if (isLoading) return <></>;
  if (isError) return <></>;
  if (!isSuccess) throw new Error("Something went wrong");
  if (!data.canUpdate) return <></>;

  return (
    <Fab
      color="primary"
      aria-label="create-order"
      onClick={handleClick}
      variant="extended"
      disabled={isSubmitting}
    >
      <Stack direction="row" spacing={1}>
        {data.isConfirmed ? <OrdersConfirmedIcon /> : <ConfirmOrdersIcon />}
        {data.isConfirmed ? (
          <Typography>Orders Confirmed</Typography>
        ) : (
          <Typography>Confirm Orders</Typography>
        )}
      </Stack>
    </Fab>
  );
};

export { ConfirmOrdersAction };
