import { createContext } from "react";
import { GameDetailContextType } from "./game-detail.context.types";

const GameDetailContext = createContext<GameDetailContextType | undefined>(undefined);

export { GameDetailContext };