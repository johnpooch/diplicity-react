import { appId } from "../../services";
import { service } from "../store"

const PREFER_CACHED_VALUE = true;

const createNewToken = (token: string) => ({
    Value: token,
    Disabled: false,
    Note: "Created via diplicity-react/browser configuration on " + new Date(),
    App: appId,
    MessageConfig: {
        BodyTemplate: "",
        TitleTemplate: "",
        ClickActionTemplate: "",
        DontSendNotification: true,
        DontSendData: false,
    },
    PhaseConfig: {
        BodyTemplate: "",
        TitleTemplate: "",
        ClickActionTemplate: "",
        DontSendNotification: true,
        DontSendData: false,
    },
    ReplaceToken: "",
})

const useFcmTokenReceivedMutation = () => {
    const [getRootQueryLazy] = service.endpoints.getRoot.useLazyQuery()
    const [getUserConfigQueryLazy] = service.endpoints.getUserConfig.useLazyQuery()
    const [update, mutation] = service.endpoints.updateUserConfig.useMutation();

    const handleFcmTokenReceived = async (token: string, enabled?: boolean) => {
        const user = await getRootQueryLazy(undefined, PREFER_CACHED_VALUE).unwrap();
        const userConfig = await getUserConfigQueryLazy(user.Id, PREFER_CACHED_VALUE).unwrap();
        const newToken = createNewToken(token);
        const existingToken = userConfig.FCMTokens?.find(t => t.App === appId);
        if (typeof enabled === "undefined") {
            newToken.Disabled = existingToken?.Disabled ?? false;
        } else {
            newToken.Disabled = !enabled;
        }
        const updatedTokens = userConfig.FCMTokens?.filter(t => t.App !== appId) ?? [];
        updatedTokens.push(newToken);
        await update({ ...userConfig, FCMTokens: updatedTokens });
    }
    return [handleFcmTokenReceived, mutation] as const;
}
export { useFcmTokenReceivedMutation };