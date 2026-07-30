import { AxiosError } from "axios";

export const isNetworkError = (error: unknown): boolean =>
  error instanceof AxiosError && error.code === AxiosError.ERR_NETWORK;
