import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { store } from '../store/store';
import { selectAuth, authSlice } from '../store/auth';

const diplictityApiBaseUrl = import.meta.env.VITE_DIPLICITY_API_BASE_URL;

const axiosInstance = axios.create({
  baseURL: diplictityApiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = selectAuth(store.getState()).accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
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

      const refreshToken = selectAuth(store.getState()).refreshToken;

      try {
        const refreshResult = await axios.post(
          `${diplictityApiBaseUrl}/api/token/refresh/`,
          {
            refresh: refreshToken,
          }
        );

        if (refreshResult.data?.access) {
          const { access } = refreshResult.data;
          store.dispatch(authSlice.actions.updateAccessToken(access));

          processQueue(null);
          isRefreshing = false;

          return axiosInstance(originalRequest);
        }
      } catch (refreshError) {
        processQueue(refreshError as Error);
        store.dispatch(authSlice.actions.logout());
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
