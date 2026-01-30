import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { LandingPage } from "@/components/LandingPage";
import { WizardLayout } from "@/components/wizard/WizardLayout";
import { PhaseSetup } from "@/components/wizard/PhaseSetup";
import { PhaseProvinces } from "@/components/wizard/PhaseProvinces";

const WIZARD_PHASES = [
  { path: "0", title: "Variant Setup", component: PhaseSetup },
  { path: "1", title: "Province Details", component: PhaseProvinces },
];

function WizardOutlet() {
  return (
    <WizardLayout>
      <Outlet />
    </WizardLayout>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    path: "/phase",
    element: <WizardOutlet />,
    children: [
      {
        index: true,
        element: <Navigate to="0" replace />,
      },
      ...WIZARD_PHASES.map(({ path, component: Component }) => ({
        path,
        element: <Component />,
      })),
    ],
  },
]);

export { WIZARD_PHASES };
