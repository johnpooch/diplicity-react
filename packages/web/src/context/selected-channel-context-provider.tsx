import React from "react";
import { useParams } from "react-router";
import { SelectedChannelContext } from "../common";

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

export { SelectedChannelContextProvider };
