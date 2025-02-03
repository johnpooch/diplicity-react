import { service } from "./common";

/**
 * Formats an order object into a human-readable string.
 */
const formatOrderText = (order: {
    source: string;
    orderType: string;
    target?: string;
    aux?: string;
}) => {
    if (order.orderType === "Hold") {
        return `${order.source} Hold`;
    }
    if (order.orderType === "Support") {
        return `${order.source} Support ${order.target} ${order.aux}`;
    }
    return `${order.source} ${order.orderType} to ${order.target}`;
}

/**
 * Transforms a resolution string into a human-readable label
 * and extracts `by` if it exists.
 */
const transformResolution = (resolution: string): { outcome: string, by?: string } => {
    const resolutionMap: Record<string, string> = {
        OK: "Succeeded",
        ErrBounce: "Bounced",
        ErrSupportBroken: "Support broken",
        ErrInvalidSupporteeOrder: "Invalid order",
    }

    const regex = /([^:]+)(?::(.+))?/;

    const match = resolution.match(regex);
    if (!match) throw new Error(`Unexpected resolution: ${resolution}`);
    return {
        outcome: resolutionMap[match[1]],
        by: match[2],
    };
};

const getChannelDisplayName = (channel: typeof service.endpoints.listChannels.Types.ResultType[number],
    variant: typeof service.endpoints.listVariants.Types.ResultType[number],
    member: typeof service.endpoints.getGame.Types.ResultType["Members"][number]) => {

    const sortedVariantNations = [...variant.Nations].sort().join(",");
    const sortedChannelMembers = [...channel.Members].sort().join(",");

    const isPublicPress = sortedVariantNations === sortedChannelMembers;

    if (isPublicPress) return "Public Press";


    const removeNation = (name: string, nation: string) => {
        return name
            .replace(nation, "")
            .replace(/,,/, ",")
            .replace(/^,/, "")
            .replace(/,$/, "");
    };

    let displayName = channel.Name;
    if (member) {
        displayName = removeNation(channel.Name, member.Nation);
    }

    displayName = displayName.replace(/,/g, ", ");
    return displayName;
}

export { formatOrderText, transformResolution, getChannelDisplayName };