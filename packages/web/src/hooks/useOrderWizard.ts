import { useState, useMemo } from "react";
import { deriveWizardStep, OrderOption } from "../utils/deriveWizardStep";

const NO_SELECTIONS: Record<string, string> = {};

function useOrderWizard(
  orders: OrderOption[],
  fieldOrder: Record<string, string[]>,
  scope: number | null
) {
  const [state, setState] = useState<{
    scope: number | null;
    selections: Record<string, string>;
  }>({ scope, selections: NO_SELECTIONS });

  if (state.scope !== scope) {
    setState({ scope, selections: NO_SELECTIONS });
  }

  const selections = state.scope === scope ? state.selections : NO_SELECTIONS;

  const step = useMemo(
    () => deriveWizardStep(orders, fieldOrder, selections),
    [orders, fieldOrder, selections]
  );

  const select = (value: string) => {
    if (!step.nextField) return;
    setState({
      scope,
      selections: { ...selections, [step.nextField]: value },
    });
  };

  const reset = () => setState({ scope, selections: NO_SELECTIONS });

  return { ...step, selections, select, reset };
}

export { useOrderWizard };
