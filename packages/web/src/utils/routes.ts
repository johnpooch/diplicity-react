export const CREATE_GAME_PARAM = {
  variantId: "variantId",
  private: "private",
} as const;

export function createGamePath(params: { variantId: string; private: boolean }): string {
  return `/create-game?${CREATE_GAME_PARAM.variantId}=${params.variantId}&${CREATE_GAME_PARAM.private}=${params.private}`;
}
