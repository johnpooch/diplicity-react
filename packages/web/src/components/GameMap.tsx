import { useRequiredParams } from "../hooks";
import { useState, useRef, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { determineRenderableProvinces } from "../utils/provinces";
import { InteractiveMapZoomWrapper } from "./InteractiveMap/InteractiveMapZoomWrapper";
import { FloatingMenu, FloatingMenuItem } from "./FloatingMenu";
import {
  useGameRetrieve,
  useVariantsList,
  useGamePhaseRetrieve,
  useGamePhaseStatesList,
  useGameOrdersList,
  useGameOrdersCreate,
  getGameOrdersListQueryKey,
  Order,
  OrderOption,
} from "../api/generated/endpoints";

type OrderState = {
  selected: string[];
  options: readonly OrderOption[];
  step: string | null;
  complete: boolean;
  title: string | null;
};

const GameMap: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const selectedPhase = Number(phaseId);

  const queryClient = useQueryClient();

  const { data: game } = useGameRetrieve(gameId);
  const { data: variants } = useVariantsList();
  const { data: phase } = useGamePhaseRetrieve(gameId, selectedPhase);
  const { data: phaseStates } = useGamePhaseStatesList(gameId);
  const { data: orders } = useGameOrdersList(gameId, selectedPhase);

  const containerRef = useRef<HTMLDivElement>(null);

  const [orderState, setOrderState] = useState<OrderState | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ x: number; y: number } | null>(null);
  const createOrderMutation = useGameOrdersCreate();

  const handleOrderResult = (result: Order) => {
    if (result.complete) {
      if (result.title) {
        toast.success(result.title);
      }
      setOrderState(null);
      setMenuPosition(null);
      queryClient.invalidateQueries({
        queryKey: getGameOrdersListQueryKey(gameId, selectedPhase),
      });
    } else {
      setOrderState({
        selected: result.selected ?? [],
        options: result.options ?? [],
        step: result.step ?? null,
        complete: result.complete ?? false,
        title: result.title ?? null,
      });
    }
  };

  const variant = variants?.find(v => v.id === game?.variantId);

  const renderableProvinces = useMemo(() => {
    if (!variant) return [];

    const allProvinces = variant.provinces;
    const highlightedProvinceIds = orderState?.options?.map(o => o.value) ?? [];

    return determineRenderableProvinces(allProvinces, highlightedProvinceIds);
  }, [variant?.provinces, orderState?.options]);

  const handleProvinceClick = async (
    province: string,
    event: React.MouseEvent<SVGPathElement>
  ) => {
    if (!renderableProvinces.includes(province)) {
      return;
    }

    const orderableProvince = phaseStates
      ?.flatMap(ps => ps.orderableProvinces)
      .find(p => p.id === province);
    const options = orderState?.options;

    if (orderState) {
      if (options?.some(o => o.value === province)) {
        const result = await createOrderMutation.mutateAsync({
          gameId,
          data: {
            selected: [...(orderState.selected ?? []), province],
          },
        });
        handleOrderResult(result);
      }
    } else {
      if (orderableProvince) {
        // Capture click position for the floating menu
        if (containerRef.current) {
          const containerRect = containerRef.current.getBoundingClientRect();
          const x = event.clientX - containerRect.left;
          const y = event.clientY - containerRect.top;
          if (x > 0 && y > 0) {
            setMenuPosition({ x, y });
          }
        }

        const result = await createOrderMutation.mutateAsync({
          gameId,
          data: {
            selected: [province],
          },
        });
        handleOrderResult(result);
      }
    }
  };

  const handleSelectOrderOption = async (option: string) => {
    if (orderState) {
      const result = await createOrderMutation.mutateAsync({
        gameId,
        data: {
          selected: [...(orderState.selected ?? []), option],
        },
      });
      handleOrderResult(result);
    }
  };

  const handleCloseMenu = () => {
    setOrderState(null);
    setMenuPosition(null);
  };

  const showMenu =
    (orderState?.step === "select-order-type" ||
      orderState?.step === "select-unit-type") &&
    menuPosition !== null;

  return (
    <div ref={containerRef} className="relative w-full h-full">
      {game && variant && phase && orders && (
        <>
          <InteractiveMapZoomWrapper
            interactiveMapProps={{
              interactive: true,
              variant: variant,
              phase: phase,
              orders: orders,
              selected: orderState?.selected ?? [],
              onClickProvince: handleProvinceClick,
              renderableProvinces: renderableProvinces,
              highlighted: orderState?.options?.map(o => o.value) ?? [],
            }}
          />
          <FloatingMenu
            open={showMenu}
            x={menuPosition?.x ?? 0}
            y={menuPosition?.y ?? 0}
            container={containerRef.current}
            onClose={handleCloseMenu}
          >
            {orderState?.options?.map(o => (
              <FloatingMenuItem
                key={o.value}
                onClick={() => handleSelectOrderOption(o.value)}
              >
                {o.label}
              </FloatingMenuItem>
            ))}
          </FloatingMenu>
        </>
      )}
    </div>
  );
};

export { GameMap };
