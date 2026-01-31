import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { LandingPage } from "@/components/LandingPage";
import { WizardLayout } from "@/components/wizard/WizardLayout";
import { PhaseSetup } from "@/components/wizard/PhaseSetup";
import { PhaseProvinces } from "@/components/wizard/PhaseProvinces";
import { PhaseTextAssoc } from "@/components/wizard/PhaseTextAssoc";
import { PhaseAdjacencies } from "@/components/wizard/PhaseAdjacencies";
import { PhaseVisualEditor } from "@/components/wizard/PhaseVisualEditor";

const WIZARD_PHASES = [
  { path: "0", title: "Variant Setup", component: PhaseSetup },
  { path: "1", title: "Province Details", component: PhaseProvinces },
  { path: "2", title: "Text Association", component: PhaseTextAssoc },
  { path: "3", title: "Adjacencies", component: PhaseAdjacencies },
  { path: "4", title: "Visual Editor", component: PhaseVisualEditor },
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
