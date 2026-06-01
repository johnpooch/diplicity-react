import React from "react";
import { useParams } from "react-router";

import { VariantEdit } from "./VariantCreate";

const VariantEditRoute: React.FC = () => {
  const { variantId } = useParams<{ variantId: string }>();
  if (!variantId) return null;
  return <VariantEdit variantId={variantId} />;
};

export { VariantEditRoute };
