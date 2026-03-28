import { useRequiredParams } from "../hooks";
import { useRef, useMemo, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { determineRenderableProvinces } from "../utils/provinces";
import { InteractiveMapZoomWrapper } from "./InteractiveMap/InteractiveMapZoomWrapper";
import { FloatingMenu, FloatingMenuItem } from "./FloatingMenu";
import {
  useGameRetrieve,
  useVariantsList,
  useGamePhaseRetrieve,
  useGameOrdersList,
  useGameOrdersCreate,
  getGameOrdersListQueryKey,
  useGameOptionsRetrieve,
} from "../api/generated/endpoints";
import { useOrderWizard } from "../hooks/useOrderWizard";

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
  const { data: orders } = useGameOrdersList(gameId, selectedPhase);
  const { data: optionsData } = useGameOptionsRetrieve(gameId);

  const containerRef = useRef<HTMLDivElement>(null);
  const [menuPosition, setMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const createOrderMutation = useGameOrdersCreate();

  const wizard = useOrderWizard(
    optionsData?.orders ?? [],
    optionsData?.fieldOrder ?? {}
  );

  const variant = variants?.find((v) => v.id === game?.variantId);

  const isWizardActive = Object.keys(wizard.selections).length > 0;

  const highlightedIds = useMemo(() => {
    if (!isWizardActive) return [];
    if (
      wizard.nextField === "target" ||
      wizard.nextField === "aux"
    ) {
      return wizard.choices.map((c) => c.id);
    }
    return [];
  }, [isWizardActive, wizard.nextField, wizard.choices]);

  const renderableProvinces = useMemo(() => {
    if (!variant) return [];
    return determineRenderableProvinces(variant.provinces, highlightedIds);
  }, [variant, highlightedIds]);

  useEffect(() => {
    if (!wizard.isComplete || wizard.selectedArray.length === 0) return;
    createOrderMutation
      .mutateAsync({
        gameId,
        data: { selected: wizard.selectedArray },
      })
      .then((order) => {
        toast.success(order.title ?? "Order created");
        wizard.reset();
        setMenuPosition(null);
        queryClient.invalidateQueries({
          queryKey: getGameOrdersListQueryKey(gameId, selectedPhase),
        });
      })
      .catch(() => {
        toast.error("Failed to create order");
        wizard.reset();
        setMenuPosition(null);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
  }, [wizard.isComplete]);

  const captureMenuPosition = (event: React.MouseEvent<SVGPathElement>) => {
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const x = event.clientX - containerRect.left;
      const y = event.clientY - containerRect.top;
      if (x > 0 && y > 0) {
        setMenuPosition({ x, y });
      }
    }
  };

  const handleProvinceClick = (
    province: string,
    event: React.MouseEvent<SVGPathElement>
  ) => {
    if (!renderableProvinces.includes(province)) {
      return;
    }

    if (wizard.nextField === "source") {
      if (!wizard.choices.some((c) => c.id === province)) return;
      captureMenuPosition(event);
      wizard.select(province);
    } else if (
      wizard.nextField === "target" ||
      wizard.nextField === "aux"
    ) {
      if (wizard.choices.some((c) => c.id === province)) {
        wizard.select(province);
      }
    } else if (
      (wizard.nextField === "orderType" ||
        wizard.nextField === "unitType" ||
        wizard.nextField === "namedCoast") &&
      province === wizard.resolvedSelections["source"]
    ) {
      captureMenuPosition(event);
    }
  };

  const handleSelectOrderOption = (option: string) => {
    wizard.select(option);
  };

  const handleCloseMenu = () => {
    wizard.reset();
    setMenuPosition(null);
  };

  const showMenu =
    (wizard.nextField === "orderType" ||
      wizard.nextField === "unitType" ||
      wizard.nextField === "namedCoast") &&
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
              selected: wizard.selectedArray,
              onClickProvince: handleProvinceClick,
              renderableProvinces: renderableProvinces,
              highlighted: highlightedIds,
            }}
          />
          <FloatingMenu
            open={showMenu}
            x={menuPosition?.x ?? 0}
            y={menuPosition?.y ?? 0}
            container={containerRef.current}
            onClose={handleCloseMenu}
          >
            {wizard.choices.map((c) => (
              <FloatingMenuItem
                key={c.id}
                onClick={() => handleSelectOrderOption(c.id)}
              >
                {c.label}
              </FloatingMenuItem>
            ))}
          </FloatingMenu>
        </>
      )}
    </div>
  );
};

export { GameMap };
