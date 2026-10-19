import { useMemo } from "react";
import type { BoardState, OrderDetail } from "@/api";
import { toRenderState } from "@/board/toRenderState";
import { MapView } from "@/components/MapView";

interface BoardProps {
  board: BoardState;
  orders: OrderDetail[];
}

export const Board: React.FC<BoardProps> = ({ board, orders }) => {
  const state = useMemo(() => toRenderState(board, orders), [board, orders]);
  return <MapView state={state} />;
};
