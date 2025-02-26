import React from "react";

type CreateChannelContextType = {
  selectedMembers: string[];
  setSelectedMembers: React.Dispatch<React.SetStateAction<string[]>>;
};

const CreateChannelContext = React.createContext<
  CreateChannelContextType | undefined
>(undefined);

const useCreateChannelContext = () => {
  const context = React.useContext(CreateChannelContext);
  if (!context) {
    throw new Error("useCreateChannelContext must be used within a CreateChannelContextProvider");
  }
  return context;
}

export { CreateChannelContext, useCreateChannelContext };