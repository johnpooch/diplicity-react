import { Fab } from "@mui/material";
import { Add as CreateOrderIcon } from "@mui/icons-material";
import { useCreateOrderAction } from "./CreateOrderAction.hook";

const CreateOrderAction: React.FC = () => {
  const { isLoading, isError, data, handleClick } = useCreateOrderAction();

  if (isLoading) return <></>;
  if (isError) return <></>;
  if (!data?.canCreateOrder) return <></>;

  return (
    <Fab color="primary" aria-label="create-order" onClick={handleClick}>
      <CreateOrderIcon />
    </Fab>
  );
};

export { CreateOrderAction };
