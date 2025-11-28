import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { MenuItem, Stack } from "@mui/material";
import { createUseStyles } from "./utils/styles";
import { FloatingMenu } from "./FloatingMenu";
import { useState, useRef, useEffect, useMemo } from "react";
import { determineRenderableProvinces } from "../utils/provinces";
import { InteractiveMapZoomWrapper } from "./InteractiveMap/InteractiveMapZoomWrapper";

const useStyles = createUseStyles(() => ({
  mapContainer: {
    position: "relative",
    width: "100%",
    height: "100%",
  },
}));

const GameMap: React.FC = () => {
  const styles = useStyles({});

  const { gameId, gameRetrieveQuery } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const [menuPosition, setMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  const [createOrder, createOrderQuery] =
    service.endpoints.gameOrdersCreate.useMutation({
      fixedCacheKey: "create-interactive",
    });

  const listVariantsQuery = service.endpoints.variantsList.useQuery();

  const phaseQuery = service.endpoints.gamePhaseRetrieve.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  const phaseStatesListQuery = service.endpoints.gamePhaseStatesList.useQuery({
    gameId: gameId,
  });

  const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  useEffect(() => {
    if (createOrderQuery.data?.complete) {
      createOrderQuery.reset();
    }
  }, [createOrderQuery.data]);

  const variant = listVariantsQuery.data?.find(
    v => v.id === gameRetrieveQuery.data?.variantId
  );

  // Calculate which provinces should be rendered based on highlighted options
  const renderableProvinces = useMemo(() => {
    if (!variant) return [];

    const allProvinces = variant.provinces;
    const highlightedProvinceIds =
      createOrderQuery.data?.options?.map(o => o.value) ?? [];

    return determineRenderableProvinces(allProvinces, highlightedProvinceIds);
  }, [variant?.provinces, createOrderQuery.data?.options]);

  const handleProvinceClick = (
    province: string,
    event: React.MouseEvent<SVGPathElement>
  ) => {
    // Only process clicks for renderable provinces
    if (!renderableProvinces.includes(province)) {
      return;
    }
    // Always calculate and store the click position first, regardless of order state
    let x = 0,
      y = 0;
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      x = event.clientX - containerRect.left;
      y = event.clientY - containerRect.top;
    }

    const orderableProvince = phaseStatesListQuery.data
      ?.flatMap(ps => ps.orderableProvinces)
      .find(p => p.id === province);
    const options = createOrderQuery.data?.options;

    // If the createInteractive query has data, only allow options to be selected. If not, allow orderable provinces to be selected.
    if (createOrderQuery.data) {
      if (options?.some(o => o.value === province)) {
        createOrder({
          gameId,
          order: {
            selected: [...(createOrderQuery.data?.selected ?? []), province],
          },
        });
      }
    } else {
      if (orderableProvince) {
        // Only update position if coordinates are reasonable (not 0,0 from a bad calculation)
        if (x > 0 && y > 0) {
          setMenuPosition({ x, y });
        }
        createOrder({
          gameId,
          order: {
            selected: [province],
          },
        });
      }
    }
  };

  const handleSelectOrderOption = (option: string) => {
    if (createOrderQuery.data) {
      createOrder({
        gameId,
        order: {
          selected: [...(createOrderQuery.data.selected ?? []), option],
        },
      });
    }
  };

  return (
    <Stack ref={containerRef} sx={styles.mapContainer}>
      {gameRetrieveQuery.data && variant && phaseQuery.data && ordersListQuery.data && (
        <>
          <InteractiveMapZoomWrapper
            interactiveMapProps={{
              interactive: true,
              // style: { width: "100%", height: "100%" },
              variant: variant,
              phase: phaseQuery.data,
              orders: ordersListQuery.data,
              selected: createOrderQuery.data?.selected ?? [],
              onClickProvince: handleProvinceClick,
              renderableProvinces: renderableProvinces,
              highlighted:
                createOrderQuery.data?.options?.map(o => o.value) ?? [],
            }}
          />
          <FloatingMenu
            open={
              (createOrderQuery.data?.step === "select-order-type" ||
                createOrderQuery.data?.step === "select-unit-type") &&
              menuPosition !== null
            }
            onClose={() => {
              createOrderQuery.reset();
              setMenuPosition(null);
            }}
            x={menuPosition?.x ?? 0}
            y={menuPosition?.y ?? 0}
            container={containerRef.current}
          >
            {createOrderQuery.data?.options.map(o => (
              <MenuItem
                key={o.value}
                onClick={() => handleSelectOrderOption(o.value)}
              >
                {o.label}
              </MenuItem>
            ))}
          </FloatingMenu>
        </>
      )}
    </Stack>
  );
};

export { GameMap };
