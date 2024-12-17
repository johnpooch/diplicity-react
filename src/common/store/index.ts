import * as thunkActions from "./actions"
import { modalActions } from "./modal";
import { feedbackActions } from "./feedback";
export { selectFeedback } from "./feedback";
export { selectModal } from "./modal"
export * from "./store";
export * from "./service";
export * as Service from "./service.types";

export const actions = {
    ...thunkActions,
    ...feedbackActions,
    ...modalActions
};