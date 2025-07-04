import { NavigateFunction } from "react-router";
import * as Desktop from "../desktop";

type GameDetailSecondaryScreenLayoutProps = {
  title: string;
  onNavigateBack: (navigate: NavigateFunction, gameId: string) => void;
};

const GameDetailSecondaryScreenLayout: React.FC<
  GameDetailSecondaryScreenLayoutProps
> = props => {
  return <Desktop.GameDetailSecondaryScreenLayout {...props} />;
};

export { GameDetailSecondaryScreenLayout };
