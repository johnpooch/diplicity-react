import React from "react";
import BrowseGames from "./pages/BrowseGames";
import { Route, Routes } from "react-router";

const Router: React.FC = () => {
  return (
    <Routes>
      <Route index element={<BrowseGames games={[]} />} />
    </Routes>
  );
};

export default Router;
