import { useMemo } from "react";
import type { BoardState, OrderDetail } from "@/api";
import { DiplicityMap } from "@/board/mapRenderer";
import { toRenderState } from "@/board/toRenderState";
import CLASSICAL_DSVG from "@/board/classical.d.svg?raw";

interface BoardProps {
  board: BoardState;
  orders: OrderDetail[];
}

const map = new DiplicityMap(CLASSICAL_DSVG);

export const Board: React.FC<BoardProps> = ({ board, orders }) => {
  const svg = useMemo(() => map.render(toRenderState(board, orders)), [board, orders]);
  return (
    <div
      className="h-full [&>svg]:h-full [&>svg]:w-full"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
