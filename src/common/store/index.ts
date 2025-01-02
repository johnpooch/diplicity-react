import { feedbackActions } from "./feedback";
export { selectFeedback } from "./feedback";
export * from "./store";
export * from "./service";
export * as Service from "./service.types";

export const actions = {
    ...feedbackActions,
};