import { Options } from "../store/service.types";

const getOptions = (options: Options, selectedOptions: string[]): { options: string[], type: string | undefined } => {
    let currentOptions = options;
    let type: string | undefined = "Province";

    for (const selectedOption of selectedOptions) {
        if (!currentOptions[selectedOption]) {
            throw new Error("Invalid selected options")
        }
        if (currentOptions[selectedOption] && currentOptions[selectedOption].Next && Object.keys(currentOptions[selectedOption].Next).length > 0) {
            currentOptions = currentOptions[selectedOption].Next;
            type = Object.values(currentOptions)[0].Type;
        } else {
            currentOptions = [] as unknown as Options;
            type = undefined;
        }
    }

    return { options: Object.keys(currentOptions), type };
};

export { getOptions };