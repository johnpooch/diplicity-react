import { createBrowserRouter, useParams } from "react-router-dom";
import { findVariant } from "@/manifest";
import { Index } from "@/screens/Index";
import { NotFound } from "@/screens/NotFound";

const PrototypeRoute: React.FC = () => {
  const { prototypeSlug, variantSlug, stateSlug } = useParams();
  const match = findVariant(prototypeSlug, variantSlug);

  if (!match) {
    return <NotFound />;
  }

  const { variant } = match;
  const state = variant.states.find(item => item.slug === stateSlug);

  if (stateSlug && !state) {
    return <NotFound />;
  }

  return variant.render(state?.slug ?? variant.states[0].slug);
};

export const router = createBrowserRouter([
  { path: "/", element: <Index /> },
  { path: "/:prototypeSlug/:variantSlug", element: <PrototypeRoute /> },
  {
    path: "/:prototypeSlug/:variantSlug/:stateSlug",
    element: <PrototypeRoute />,
  },
  { path: "*", element: <NotFound /> },
]);
