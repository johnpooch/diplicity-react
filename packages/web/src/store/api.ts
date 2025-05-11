// Or from '@reduxjs/toolkit/query' if not using the auto-generated hooks
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { authSlice, selectAuth } from './auth';

const diplictityApiBaseUrl = import.meta.env.VITE_DIPLICITY_API_BASE_URL;

const baseQuery = fetchBaseQuery({
    baseUrl: diplictityApiBaseUrl,
    prepareHeaders: async (headers, { getState }) => {
        const token = selectAuth(getState() as Parameters<typeof selectAuth>[0]).accessToken;
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }
        return headers;
    },
    mode: "cors",
});

const baseQueryWithReauth = async (args: Parameters<typeof baseQuery>[0], api: Parameters<typeof baseQuery>[1], extraOptions: Parameters<typeof baseQuery>[2]) => {
    let result = await baseQuery(args, api, extraOptions);

    if (result.error && result.error.status === 401) {
        const refreshResult = await baseQuery("/api/token/refresh/", api, extraOptions);

        if (refreshResult.data) {
            const { access } = refreshResult.data as { access: string };
            api.dispatch(authSlice.actions.updateAccessToken(access));
            result = await baseQuery(args, api, extraOptions);
        } else {
            api.dispatch(authSlice.actions.logout());
        }
    }
    return result;
}



const api = createApi({
    baseQuery: baseQueryWithReauth,
    endpoints: () => ({}),
})


export { api }