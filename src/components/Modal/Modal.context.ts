import React from "react";
import { ModalContextType } from "./Modal.types";

const ModalContext = React.createContext<ModalContextType | undefined>(
    undefined
);

export { ModalContext };