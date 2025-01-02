import React from "react";
import { Modal as MuiModal, Box, Stack } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { ModalContext } from "./Modal.context";

const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  boxShadow: 24,
  p: 4,
};

const Modal: React.FC<{
  name: string;
  // Update children to be a render prop that passes the value and onClose function
  // children: React.ReactNode;
  children: (props: {
    value: string | null;
    onClose: () => void;
  }) => React.ReactNode;
}> = (props) => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const isOpen = queryParams.has(props.name);
  const value = queryParams.get(props.name);

  const onClose = () => {
    const searchParams = new URLSearchParams(location.search);
    searchParams.delete(props.name);
    navigate({ search: searchParams.toString() });
  };

  return (
    <MuiModal open={isOpen} onClose={onClose}>
      <Box sx={style}>
        <Stack spacing={2}>
          <ModalContext.Provider value={{ onClose, value }}>
            {props.children({ value, onClose })}
          </ModalContext.Provider>
        </Stack>
      </Box>
    </MuiModal>
  );
};

export { Modal };
