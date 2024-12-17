import React, { createContext, useContext, useState } from "react";

type GlobalModalContextType = {
  openModal: (modalType: string, id: string) => void;
  closeModal: () => void;
  modalType: string | null;
  modalId: string | null;
};

const GlobalModalContext = createContext<GlobalModalContextType | undefined>(
  undefined
);

export const useGlobalModal = (): GlobalModalContextType => {
  const context = useContext(GlobalModalContext);
  if (!context) {
    throw new Error("useGlobalModal must be used within a GlobalModalProvider");
  }
  return context;
};

export const GlobalModalProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [modalType, setModalType] = useState<string | null>(null);
  const [modalId, setModalId] = useState<string | null>(null);

  const openModal = (type: string, id: string) => {
    setModalType(type);
    setModalId(id);
  };

  const closeModal = () => {
    setModalType(null);
    setModalId(null);
  };

  return (
    <GlobalModalContext.Provider
      value={{ openModal, closeModal, modalType, modalId }}
    >
      {children}
    </GlobalModalContext.Provider>
  );
};
