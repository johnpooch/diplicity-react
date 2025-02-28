import React from "react";

/**
 * Context for managing the state of the create channel screen. The state has
 * to be lifted into context so the controls and members list can be rendered
 * separately.
 */
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

type CreateChannelContextType = {
  selectedMembers: string[];
  setSelectedMembers: React.Dispatch<React.SetStateAction<string[]>>;
};

export { CreateChannelContext, useCreateChannelContext };