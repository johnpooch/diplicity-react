import { z } from "zod";
import { apiResponseSchema } from "./common";

const fcmTokenConfig = z.object({
    ClickActionTemplate: z.string(),
    TitleTemplate: z.string(),
    BodyTemplate: z.string(),
    DontSendData: z.boolean(),
    DontSendNotification: z.boolean(),
});

const fcmTokenSchema = z.object({
    Value: z.string(),
    Disabled: z.boolean(),
    Note: z.string(),
    App: z.string(),
    MessageConfig: fcmTokenConfig,
    PhaseConfig: fcmTokenConfig,
    ReplaceToken: z.string()
});

const userConfigSchema = z.object({
    FCMTokens: z.nullable(z.array(fcmTokenSchema)).optional(),
    MailConfig: z.object({
        Enabled: z.boolean().optional(),
        UnsubscribeConfig: z.object({
            RedirectTemplate: z.string(),
            HTMLTemplate: z.string(),
        }),
        MessageConfig: z.object({
            TextBodyTemplate: z.string(),
        }),
        PhaseConfig: z.object({
            TextBodyTemplate: z.string(),
        }),
    }).optional(),
    MessageConfig: z.object({
        SubjectTemplate: z.string(),
        TextBodyTemplate: z.string(),
        HTMLBodyTemplate: z.string(),
    }).optional(),
    PhaseConfig: z.object({
        SubjectTemplate: z.string(),
        TextBodyTemplate: z.string(),
        HTMLBodyTemplate: z.string(),
    }).optional(),
    Colors: z.array(z.string()).nullable(),
    PhaseDeadlineWarningMinutesAhead: z.number().optional(),
})

const getUserConfigSchema = apiResponseSchema(userConfigSchema).transform((response) => {
    // Get the FCM token that is associated with this app and assign it to the response
    const fcmToken = response.Properties.FCMTokens?.find((token) => token.App === "diplicity-react/browser");
    const transformedProperties = { ...response.Properties, FCMToken: fcmToken };
    return { ...response, Properties: transformedProperties };
});

export { userConfigSchema, getUserConfigSchema };
