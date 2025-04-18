// Or from '@reduxjs/toolkit/query' if not using the auto-generated hooks
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { selectAuth } from './auth';

const diplictityApiBaseUrl = import.meta.env.VITE_DIPLICITY_API_BASE_URL;

const api = createApi({
    baseQuery: fetchBaseQuery({
        baseUrl: diplictityApiBaseUrl,
        prepareHeaders: async (headers, { getState }) => {
            const token = selectAuth(getState() as Parameters<typeof selectAuth>[0]).accessToken;
            if (token) {
                headers.set("Authorization", `Bearer ${token}`);
            }
            return headers;
        },
        mode: "cors",
    }),
    endpoints: () => ({}),
})

export { api }