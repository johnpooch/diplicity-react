import React from "react";
import { Outlet } from "react-router";
import { ChannelContextProvider } from "../../context/channel-context";

const ChannelLayout: React.FC = () => {
  return (
    <ChannelContextProvider>
      <Outlet />
    </ChannelContextProvider>
  );
};

export { ChannelLayout };
