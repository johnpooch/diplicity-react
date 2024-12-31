import { useLocation, useNavigate } from "react-router";
import { Fab } from "@mui/material";
import { Add as CreateOrderIcon } from "@mui/icons-material";

const CreateOrderAction: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const handleClick = () => {
    const searchParams = new URLSearchParams(location.search);
    searchParams.set("createOrder", "true");
    navigate({ search: searchParams.toString() });
  };
  return (
    <Fab color="primary" aria-label="create-order" onClick={handleClick}>
      <CreateOrderIcon />
    </Fab>
  );
};

export { CreateOrderAction };
