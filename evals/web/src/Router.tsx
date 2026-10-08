import { createBrowserRouter, Navigate, useRouteError } from "react-router-dom";
import { TriangleAlert } from "lucide-react";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { FixtureScreen } from "@/screens/FixtureScreen";
import { FixturesLayout } from "@/screens/FixturesLayout";
import { Layout } from "@/screens/Layout";
import { ReviewScreen } from "@/screens/ReviewScreen";
import { RunFixtureScreen } from "@/screens/RunFixtureScreen";
import { RunScreen } from "@/screens/RunScreen";
import { RunsScreen } from "@/screens/RunsScreen";

const RouteError: React.FC = () => {
  const error = useRouteError();
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <TriangleAlert />
        </EmptyMedia>
        <EmptyTitle>Something went wrong</EmptyTitle>
        <EmptyDescription>
          {error instanceof Error ? error.message : String(error)}. Is the API running? Start it with
          `python manage.py runserver 8001` in evals/.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <Navigate to="/fixtures" replace /> },
      {
        path: "fixtures",
        element: <FixturesLayout />,
        children: [{ path: ":fixtureId", element: <FixtureScreen /> }],
      },
      { path: "runs", element: <RunsScreen /> },
      { path: "runs/:runName", element: <RunScreen /> },
      { path: "runs/:runName/fixtures/:fixtureId", element: <RunFixtureScreen /> },
      { path: "runs/:runName/review", element: <ReviewScreen /> },
    ],
  },
]);
