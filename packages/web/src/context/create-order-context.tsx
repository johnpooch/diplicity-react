import React, { useContext, createContext, useReducer } from "react";

type CreateOrderState = {
  step: "type" | "source" | "target" | "aux" | "confirmation";
  source?: string;
  target?: string;
  aux?: string;
  type?: string;
}

type CreateOrderAction = {
  type: "UPDATE_ORDER";
  payload: string;
} | {
  type: "RESET_ORDER";
}

const createOrderReducer = (state: CreateOrderState, action: CreateOrderAction): CreateOrderState => {
  if (action.type === "RESET_ORDER") {
    return { step: "source" };
  }
  if (state.source === undefined) {
    return { ...state, source: action.payload, step: "type" };
  }
  if (state.type === undefined) {
    return {
      ...state,
      type: action.payload,
      step: action.payload === "hold" ? "confirmation" : action.payload === "move" ? "target" : "aux"
    };
  }
  if (state.target === undefined) {
    return {
      ...state,
      target: action.payload,
      step: "confirmation"
    };
  }
  if (state.aux === undefined) {
    return {
      ...state,
      aux: action.payload,
      step: "target"
    };
  }
  return state;
}

const CreateOrderContext = createContext<{
  order: CreateOrderState;
  updateOrder: (value: string) => void;
  resetOrder: () => void;
} | undefined>(
  { order: { step: "source" }, updateOrder: () => { }, resetOrder: () => { } }
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

const CreateOrderContextProvider: React.FC<{
  children: React.ReactNode | ((source: string | undefined) => React.ReactNode);
}> = ({ children }) => {
  const [order, dispatch] = useReducer<React.Reducer<CreateOrderState, CreateOrderAction>>(
    createOrderReducer,
    { step: "source" }
  );

  const updateOrder = (value: string) => {
    dispatch({ type: "UPDATE_ORDER", payload: value });
  };

  const resetOrder = () => {
    dispatch({ type: "RESET_ORDER" });
  };

  return (
    <CreateOrderContext.Provider value={{ order, updateOrder, resetOrder }}>
      {typeof children === "function" ? children(order.source) : children}
    </CreateOrderContext.Provider>
  );
};

export { CreateOrderContextProvider, useCreateOrderContext, CreateOrderContext };
