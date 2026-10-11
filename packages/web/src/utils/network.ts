import { AxiosError } from "axios";

export const isNetworkError = (error: unknown): boolean =>
  error instanceof AxiosError &&
  (error.code === AxiosError.ERR_NETWORK || error.code === AxiosError.ETIMEDOUT);

export const isNotFoundError = (error: unknown): boolean =>
  error instanceof AxiosError && error.response?.status === 404;
