import React from "react";
import { CreateChannelContext } from "../common/context/create-channel-context";

const CreateChannelContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [selectedMembers, setSelectedMembers] = React.useState<string[]>([]);

  return (
    <CreateChannelContext.Provider
      value={{ selectedMembers, setSelectedMembers }}
    >
      {children}
    </CreateChannelContext.Provider>
  );
};

export { CreateChannelContextProvider };
