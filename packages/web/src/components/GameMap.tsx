import { useRequiredParams } from "../hooks";
import { useRef, useMemo, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { determineRenderableProvinces } from "../utils/provinces";
import { buildOptimisticOrder } from "../utils/buildOptimisticOrder";
import {
  buildOrderProgressText,
  unitAbbrev,
} from "../utils/buildOrderProgressText";
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
  type Order,
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
  const bannerClearRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [menuPosition, setMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [pendingOrder, setPendingOrder] = useState<Order | null>(null);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const createOrderMutation = useGameOrdersCreate();

  const wizard = useOrderWizard(
    optionsData?.orders ?? [],
    optionsData?.fieldOrder ?? {}
  );

  const variant = variants?.find((v) => v.id === game?.variantId);

  const civilDisorderNations = useMemo(
    () =>
      (game?.members ?? [])
        .filter((m) => m.civilDisorder && m.nation)
        .map((m) => m.nation as string),
    [game?.members]
  );

  const isWizardActive = Object.keys(wizard.selections).length > 0;

  const provinceNameMap = useMemo(
    () =>
      Object.fromEntries(
        (variant?.provinces ?? []).map((p) => [p.id, p.name])
      ),
    [variant?.provinces]
  );

  const highlightedIds = useMemo(() => {
    if (!isWizardActive) return [];
    if (wizard.nextField === "target" || wizard.nextField === "aux") {
      return wizard.choices.map((c) => c.id);
    }
    return [];
  }, [isWizardActive, wizard.nextField, wizard.choices]);

  const renderableProvinces = useMemo(() => {
    if (!variant) return [];
    return determineRenderableProvinces(variant.provinces, highlightedIds);
  }, [variant, highlightedIds]);

  const showBanner = (message: string, duration = 3000) => {
    if (bannerClearRef.current) clearTimeout(bannerClearRef.current);
    setBannerMessage(message);
    bannerClearRef.current = setTimeout(() => {
      setBannerMessage(null);
      bannerClearRef.current = null;
    }, duration);
  };

  useEffect(() => {
    if (isWizardActive) {
      if (bannerClearRef.current) {
        clearTimeout(bannerClearRef.current);
        bannerClearRef.current = null;
      }
      setBannerMessage(null);
    }
  }, [isWizardActive]);

  useEffect(() => {
    return () => {
      if (bannerClearRef.current) clearTimeout(bannerClearRef.current);
    };
  }, []);

  useEffect(() => {
    if (!wizard.isComplete || wizard.selectedArray.length === 0) return;
    if (variant && phase) {
      setPendingOrder(
        buildOptimisticOrder(wizard.resolvedSelections, variant, phase)
      );
    }
    createOrderMutation
      .mutateAsync({
        gameId,
        data: { selected: wizard.selectedArray },
      })
      .then((order) => {
        queryClient.setQueryData<Order[]>(
          getGameOrdersListQueryKey(gameId, selectedPhase),
          (old) => [
            ...(old ?? []).filter((o) => o.source.id !== order.source.id),
            order,
          ]
        );
        setPendingOrder(null);
        toast.success(order.title ?? "Order created");
        wizard.reset();
        setMenuPosition(null);
      })
      .catch(() => {
        setPendingOrder(null);
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
      if (!wizard.choices.some((c) => c.id === province)) {
        if (!phase) return;
        const unit = phase.units.find((u) => u.province.id === province);
        if (unit && !game?.sandbox) {
          showBanner(
            `${unitAbbrev(unit.type)} ${unit.province.name} (${unit.nation.name})`
          );
        } else if (!unit) {
          showBanner(provinceNameMap[province] ?? province);
        }
        return;
      }
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

  const displayOrders = pendingOrder
    ? [
        ...(orders ?? []).filter(
          (o) => o.source.id !== pendingOrder.source.id
        ),
        pendingOrder,
      ]
    : orders;

  const progressText =
    phase && isWizardActive
      ? buildOrderProgressText(
          wizard.resolvedSelections,
          wizard.resolvedLabels,
          phase
        )
      : null;

  const displayBannerText = bannerMessage ?? progressText;

  return (
    <div ref={containerRef} className="relative w-full h-full">
      {game && variant && phase && orders && (
        <>
          <InteractiveMapZoomWrapper
            interactiveMapProps={{
              interactive: true,
              variant: variant,
              phase: phase,
              orders: displayOrders,
              selected: wizard.selectedArray,
              onClickProvince: handleProvinceClick,
              renderableProvinces: renderableProvinces,
              highlighted: highlightedIds,
              civilDisorderNations: civilDisorderNations,
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
      {displayBannerText !== null && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-black/70 text-white px-4 py-2 rounded-full text-sm font-medium pointer-events-none whitespace-nowrap">
          {displayBannerText}
        </div>
      )}
    </div>
  );
};

export { GameMap };
