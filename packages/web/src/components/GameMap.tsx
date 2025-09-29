import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { MenuItem, Stack, Fab } from "@mui/material";
import { Icon, IconName } from "./Icon";
import { createUseStyles } from "./utils/styles";
import { FloatingMenu } from "./FloatingMenu";
import { useState, useRef, useEffect, useMemo } from "react";
import { determineRenderableProvinces } from "../utils/provinces";
import { useResponsiveness } from "./utils/responsive";

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

  const { device } = useResponsiveness()

  const [menuPosition, setMenuPosition] = useState<{ x: number, y: number } | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(true);

  const containerRef = useRef<HTMLDivElement>(null);

  const [createOrder, createOrderQuery] =
    service.endpoints.gameOrdersCreate.useMutation({ fixedCacheKey: "create-interactive" });

  const phaseStateRetrieveQuery = service.endpoints.gamePhaseStateRetrieve.useQuery({
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

  // Calculate which provinces should be rendered based on highlighted options
  const renderableProvinces = useMemo(() => {
    if (!gameRetrieveQuery.data) return [];

    const allProvinces = gameRetrieveQuery.data.variant.provinces;
    const highlightedProvinceIds = createOrderQuery.data?.options?.map(o => o.value) ?? [];

    return determineRenderableProvinces(allProvinces, highlightedProvinceIds);
  }, [gameRetrieveQuery.data?.variant.provinces, createOrderQuery.data?.options]);

  const handleProvinceClick = (province: string, event: React.MouseEvent<SVGPathElement>) => {
    // Only process clicks for renderable provinces
    if (!renderableProvinces.includes(province)) {
      return;
    }
    // Always calculate and store the click position first, regardless of order state
    let x = 0, y = 0;
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      x = event.clientX - containerRect.left;
      y = event.clientY - containerRect.top;
    }

    const orderableProvince = phaseStateRetrieveQuery.data?.orderableProvinces.find(p => p.id === province);
    const options = createOrderQuery.data?.options;

    // If the createInteractive query has data, only allow options to be selected. If not, allow orderable provinces to be selected.
    if (createOrderQuery.data) {
      if (options?.some(o => o.value === province)) {
        createOrder({
          gameId,
          order: {
            selected: [...createOrderQuery.data?.selected ?? [], province],
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
          selected: [...createOrderQuery.data.selected ?? [], option],
        },
      });
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <Stack ref={containerRef} sx={styles.mapContainer}>
      {
        gameRetrieveQuery.data && ordersListQuery.data && (
          <>
            <div style={{
              width: "100%", height: "100%",
              overflow: isFullscreen ? "auto" : "hidden",
            }}>
              <InteractiveMap
                interactive
                variant={gameRetrieveQuery.data.variant}
                phase={gameRetrieveQuery.data.phases.find(p => p.id === selectedPhase)!}
                orders={ordersListQuery.data}
                selected={createOrderQuery.data?.selected ?? []}
                highlighted={createOrderQuery.data?.options?.map(o => o.value) ?? []}
                renderableProvinces={renderableProvinces}
                onClickProvince={handleProvinceClick}
                fullscreen={isFullscreen}
              />
            </div>
            <FloatingMenu
              open={(createOrderQuery.data?.step === "select-order-type" || createOrderQuery.data?.step === "select-unit-type") && menuPosition !== null}
              onClose={() => {
                createOrderQuery.reset();
                setMenuPosition(null);
              }}
              x={menuPosition?.x ?? 0}
              y={menuPosition?.y ?? 0}
              container={containerRef.current}
            >
              {createOrderQuery.data?.options.map(o => (
                <MenuItem key={o.value} onClick={() => handleSelectOrderOption(o.value)}>
                  {o.label}
                </MenuItem>
              ))}
            </FloatingMenu>
            <Fab
              color="primary"
              onClick={toggleFullscreen} sx={{ position: "absolute", bottom: 20, right: 20 }}>
              <Icon name={isFullscreen ? IconName.FullscreenExit : IconName.Fullscreen} />
            </Fab>
          </>
        )
      }
    </Stack >
  )
};

export { GameMap };
