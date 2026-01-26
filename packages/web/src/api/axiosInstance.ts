import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { tokenStorage } from '../auth/tokenStorage';

const diplictityApiBaseUrl = import.meta.env.VITE_DIPLICITY_API_BASE_URL;

const axiosInstance = axios.create({
  baseURL: diplictityApiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const { accessToken } = tokenStorage.getTokenState();
  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });

  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { refreshToken } = tokenStorage.getTokenState();

      try {
        const refreshResult = await axios.post(
          `${diplictityApiBaseUrl}/api/token/refresh/`,
          {
            refresh: refreshToken,
          }
        );

        if (refreshResult.data?.access) {
          const { access } = refreshResult.data;
          tokenStorage.updateAccessToken(access);

          processQueue(null);
          isRefreshing = false;

          return axiosInstance(originalRequest);
        }
      } catch (refreshError) {
        processQueue(refreshError as Error);
        tokenStorage.clearTokens();
        isRefreshing = false;
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;

export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return axiosInstance(config).then(({ data }) => data);
};
