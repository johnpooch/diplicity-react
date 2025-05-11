import { useContext, createContext } from "react";

/**
 * Context for managing the state of the create order flow.
 * 
 * @todo: We will need to add more state to this context as we add support for
 * inputting orders directly on the map.
 */
const CreateOrderContext = createContext<CreateOrderContextType | undefined>(
    undefined
);

const useCreateOrderContext = () => {
    const context = useContext(CreateOrderContext);
    if (!context) {
        throw new Error(
            "useCreateOrderContext must be used within a CreateOrderContextProvider"
        );
    }
    return context;
};

type CreateOrderContextType = {
    source: string | undefined;
    setSource: (source: string | undefined) => void;
};

export { CreateOrderContext, useCreateOrderContext };
