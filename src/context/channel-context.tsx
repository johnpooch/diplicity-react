import React, { useContext, createContext } from "react";
import { useParams } from "react-router";

type ChannelContextType = {
  channelName: string;
};

const ChannelContext = createContext<ChannelContextType | undefined>(undefined);

const ChannelContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { channelName } = useParams<{ channelName: string }>();

  if (!channelName) throw new Error("channelName is required");

  return (
    <ChannelContext.Provider value={{ channelName }}>
      {children}
    </ChannelContext.Provider>
  );
};

const useChannelContext = () => {
  const context = useContext(ChannelContext);
  if (!context) {
    throw new Error(
      "useChannelContext must be used within a ChannelContextProvider"
    );
  }
  return context;
};

export { ChannelContextProvider, useChannelContext };
