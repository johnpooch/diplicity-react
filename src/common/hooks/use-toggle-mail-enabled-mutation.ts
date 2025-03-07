import { service } from "../store";

const PREFER_CACHED_VALUE = true;

const useToggleMailEnabledMutation = () => {
    const [getRootQueryLazy] = service.endpoints.getRoot.useLazyQuery();
    const [getUserConfigQueryLazy] = service.endpoints.getUserConfig.useLazyQuery();
    const [update, mutation] = service.endpoints.updateUserConfig.useMutation();

    const handleToggleMailEnabled = async (enabled: boolean) => {
        const user = await getRootQueryLazy(undefined, PREFER_CACHED_VALUE).unwrap();
        const userConfig = await getUserConfigQueryLazy(user.Id, PREFER_CACHED_VALUE).unwrap();

        const mailConfig = {
            Enabled: enabled,
            MessageConfig: {
                ...(userConfig?.MailConfig?.MessageConfig || {}),
                TextBodyTemplate:
                    'You received a new message on Diplicity:\n\n"{{message.Body}}"\n\n\nTo view the game, visit\n\nwww.diplicity.com/game/{{game.ID.Encode}}\n\n\n\n\nTo turn off email notifications from Diplicity, visit:\n\n{{unsubscribeURL}}"',
            },
            PhaseConfig: {
                ...(userConfig?.MailConfig?.PhaseConfig || {}),
                TextBodyTemplate:
                    "{{game.Desc}} has changed state.\n\n\nTo view the game, visit\nwww.diplicity.com/game/{{game.ID.Encode}}.\n\n\n\n\nTo turn off emails notifications from Diplicity, visit:\n\n{{unsubscribeURL}}"
            }
        }
        const updatedConfig = { ...userConfig, MailConfig: mailConfig };
        await update(updatedConfig);
    }
    return [handleToggleMailEnabled, mutation] as const;
};

export { useToggleMailEnabledMutation };
