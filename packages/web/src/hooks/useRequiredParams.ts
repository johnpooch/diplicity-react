import { useParams } from "react-router";

export function useRequiredParams<
  T extends Record<string, string>,
>(): T {
  return useParams() as T;
}
