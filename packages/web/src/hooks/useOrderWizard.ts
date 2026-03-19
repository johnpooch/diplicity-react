import { useState, useMemo } from "react";
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

  const select = (value: string) => {
    if (!step.nextField) return;
    setSelections((prev) => ({ ...prev, [step.nextField!]: value }));
  };

  const reset = () => setSelections({});

  return { ...step, selections, select, reset };
}

export { useOrderWizard };
