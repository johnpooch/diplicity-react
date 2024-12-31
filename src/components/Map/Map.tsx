import { skipToken } from "@reduxjs/toolkit/query";
import { createMap } from "../../common/map/map";
import service from "../../common/store/service";
import { useParams } from "react-router";

const Map: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");
  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const listPhasesQuery = service.endpoints.listPhases.useQuery(gameId);
  const variantName = getGameQuery.data?.Variant;
  const getVariantMapSvgQuery = service.endpoints.getVariantSvg.useQuery(
    variantName ?? skipToken
  );
  const getVariantArmySvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Army" } : skipToken
  );
  const getVariantFleetSvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Fleet" } : skipToken
  );

  if (
    !listVariantsQuery.isSuccess ||
    !getGameQuery.isSuccess ||
    !listPhasesQuery.isSuccess ||
    !getVariantMapSvgQuery.isSuccess ||
    !getVariantArmySvgQuery.isSuccess ||
    !getVariantFleetSvgQuery.isSuccess
  ) {
    return null;
  }

  const variant = listVariantsQuery.data.find(
    (v) => v.Name === getGameQuery.data.Variant
  );
  if (!variant) throw new Error("Variant not found");

  const newestPhaseMeta = getGameQuery.data.NewestPhaseMeta;
  if (!newestPhaseMeta) throw new Error("Newest phase meta not found");

  const newestPhase = listPhasesQuery.data.find(
    (p) => p.PhaseOrdinal === newestPhaseMeta.PhaseOrdinal
  );

  if (!newestPhase) throw new Error("Newest phase not found");

  const xml = createMap(
    getVariantMapSvgQuery.data,
    getVariantArmySvgQuery.data,
    getVariantFleetSvgQuery.data,
    variant,
    newestPhase
  );

  return <div dangerouslySetInnerHTML={{ __html: xml }} />;
};

export { Map };
