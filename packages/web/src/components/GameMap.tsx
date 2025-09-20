import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { MenuItem, Stack } from "@mui/material";
import { createUseStyles } from "./utils/styles";
import { FloatingMenu } from "./FloatingMenu";
import { useState, useRef, useEffect } from "react";

const useStyles = createUseStyles(() => ({
  mapContainer: {
    width: "100%",
    height: "100%",
    overflow: "auto",
    minHeight: 0, // This is important for flexbox overflow to work
  },
}));

const GameMap: React.FC = () => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();

  const styles = useStyles({});
  const { selectedPhase } = useSelectedPhaseContext();

  const [menuPosition, setMenuPosition] = useState<{ x: number, y: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [createInteractive, createInteractiveQuery] =
    service.endpoints.gameOrdersCreateInteractiveCreate.useMutation({ fixedCacheKey: "create-interactive" });

  const orderableProvincesQuery = service.endpoints.gameOrderableProvincesList.useQuery({
    gameId: gameId,
  });

  const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  useEffect(() => {
    if (createInteractiveQuery.data?.completed) {
      createInteractiveQuery.reset();
    }
  }, [createInteractiveQuery.data]);

  const handleProvinceClick = (province: string, event: React.MouseEvent<SVGPathElement>) => {
    // Always calculate and store the click position first, regardless of order state
    let x = 0, y = 0;
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      x = event.clientX - containerRect.left;
      y = event.clientY - containerRect.top;
    }

    const orderableProvince = orderableProvincesQuery.data?.find(p => p.province.id === province);
    const options = createInteractiveQuery.data?.options;

    // If the createInteractive query has data, only allow options to be selected. If not, allow orderable provinces to be selected.
    if (createInteractiveQuery.data) {
      if (options?.some(o => o.value === province)) {
        createInteractive({
          gameId,
          interactiveOrderCreateRequest: {
            selected: [...createInteractiveQuery.data?.selected, province],
          },
        });
      }
    } else {
      if (orderableProvince) {

        // Only update position if coordinates are reasonable (not 0,0 from a bad calculation)
        if (x > 0 && y > 0) {
          setMenuPosition({ x, y });
        }
        createInteractive({
          gameId,
          interactiveOrderCreateRequest: {
            selected: [province],
          },
        });
      }
    }
  };

  const handleSelectOrderOption = (option: string) => {
    if (createInteractiveQuery.data) {
      createInteractive({
        gameId,
        interactiveOrderCreateRequest: {
          selected: [...createInteractiveQuery.data.selected, option],
        },
      });
    }
  };

  return (
    <Stack ref={containerRef} sx={styles.mapContainer}>
      {
        gameRetrieveQuery.data && ordersListQuery.data && (
          <>
            <InteractiveMap
              interactive
              variant={gameRetrieveQuery.data.variant}
              phase={gameRetrieveQuery.data.phases.find(p => p.id === selectedPhase)!}
              orders={ordersListQuery.data}
              selected={createInteractiveQuery.data?.selected ?? []}
              highlighted={createInteractiveQuery.data?.options?.map(o => o.value) ?? []}
              onClickProvince={handleProvinceClick}
            />
            <FloatingMenu
              open={(createInteractiveQuery.data?.step === "select-order-type" || createInteractiveQuery.data?.step === "select-unit-type") && menuPosition !== null}
              onClose={() => {
                createInteractiveQuery.reset();
                setMenuPosition(null);
              }}
              x={menuPosition?.x ?? 0}
              y={menuPosition?.y ?? 0}
              container={containerRef.current}
            >
              {createInteractiveQuery.data?.options.map(o => (
                <MenuItem key={o.value} onClick={() => handleSelectOrderOption(o.value)}>
                  {o.label}
                </MenuItem>
              ))}
            </FloatingMenu>
          </>
        )
      }
    </Stack >
  )
};

export { GameMap };
