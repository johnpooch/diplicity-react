import { createContext, useContext } from "react";

/**
 * Context to provide the currently selected channel.
 */
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

export { SelectedChannelContext, useSelectedChannelContext };
