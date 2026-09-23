import type { Order, PhaseState } from "../api/generated/endpoints";

interface OrderCount {
  submitted: number;
  total: number;
}

const countOrders = (
  phaseStates: readonly PhaseState[],
  orders: readonly Order[]
): OrderCount | null => {
  const phaseState = phaseStates.find(ps => ps.member.isCurrentUser);
  if (!phaseState) return null;

  const orderable = phaseState.orderableProvinces;
  if (orderable.length === 0) return null;

  const submitted = orderable.filter(p =>
    orders.some(o => o.source.id === p.id)
  ).length;
  const total = Math.min(phaseState.maxOrders ?? Infinity, orderable.length);

  return { submitted, total };
};

export { countOrders };
export type { OrderCount };
