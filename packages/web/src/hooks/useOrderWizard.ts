import { useState, useMemo, useCallback } from "react";
import { deriveWizardStep, OrderOption } from "../utils/deriveWizardStep";

function useOrderWizard(
  orders: OrderOption[],
  fieldOrder: Record<string, string[]>
) {
  const [selections, setSelections] = useState<Record<string, string>>({});

  const step = useMemo(
    () => deriveWizardStep(orders, fieldOrder, selections),
    [orders, fieldOrder, selections]
  );

  const select = useCallback(
    (value: string) => {
      if (!step.nextField) return;
      setSelections((prev) => ({ ...prev, [step.nextField!]: value }));
    },
    [step.nextField]
  );

  const reset = useCallback(() => setSelections({}), []);

  return { ...step, selections, select, reset };
}

export { useOrderWizard };
