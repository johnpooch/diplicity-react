import React, { createContext, useContext } from "react";
import { useParams } from "react-router";

const SelectedChannelContext = createContext<SelectedChannelContextType | undefined>(undefined);

const useSelectedChannelContext = () => {
  const context = useContext(SelectedChannelContext);
  if (!context) {
    throw new Error(
      "useSelectedChannelContext must be used within a SelectedChannelContextProvider"
    );
  }
  return context;
};

type SelectedChannelContextType = {
  channelName: string;
};

const SelectedChannelContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { channelName } = useParams<{ channelName: string }>();

  if (!channelName) throw new Error("channelName is required");

  return (
    <SelectedChannelContext.Provider value={{ channelName }}>
      {children}
    </SelectedChannelContext.Provider>
  );
};

export { SelectedChannelContextProvider, useSelectedChannelContext };
