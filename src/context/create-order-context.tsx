import React, { useContext, createContext, useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router";

type CreateOrderContextType = {
  source: string | undefined;
  setSource: (source: string | undefined) => void;
};

const CreateOrderContext = createContext<CreateOrderContextType | undefined>(
  undefined
);

const CreateOrderContextProvider: React.FC<{
  children: React.ReactNode | ((source: string | undefined) => React.ReactNode);
}> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const [source, setSource] = useState<string | undefined>(() => {
    const params = new URLSearchParams(location.search);
    const source = params.get("source");
    return source ? source : undefined;
  });

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (source === undefined) {
      params.delete("source");
    } else {
      params.set("source", source);
    }
    navigate({ search: params.toString() }, { replace: true });
  }, [source, location.search, navigate]);

  return (
    <CreateOrderContext.Provider value={{ source, setSource }}>
      {typeof children === "function" ? children(source) : children}
    </CreateOrderContext.Provider>
  );
};

const useCreateOrderContext = () => {
  const context = useContext(CreateOrderContext);
  if (!context) {
    throw new Error(
      "useCreateOrderContext must be used within a CreateOrderContextProvider"
    );
  }
  return context;
};

export { CreateOrderContextProvider, useCreateOrderContext };
