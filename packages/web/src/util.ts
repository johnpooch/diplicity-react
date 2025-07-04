import { orderSlice, Phase, Variant } from "./store";
import { adjectives, conflictSynonyms, nouns } from "./terms";

function capitalize(s: string) {
    return s.slice(0, 1).toUpperCase() + s.slice(1);
}

function randomOf(ary: string[]) {
    return ary[Math.floor(Math.random() * ary.length)];
}

// Get the phase with the highest ordinal
function getCurrentPhase(phases: Phase[]) {
    return phases.reduce((max, phase) => {
        if (phase.ordinal > max.ordinal) {
            return phase;
        }
        return max;
    }, phases[0]);
}

function dziemba_levenshtein(a: string, b: string) {
    let tmp;
    if (a.length === 0) {
        return b.length;
    }
    if (b.length === 0) {
        return a.length;
    }
    if (a.length > b.length) {
        tmp = a;
        a = b;
        b = tmp;
    }
    let i,
        j,
        res,
        // eslint-disable-next-line prefer-const
        alen = a.length,
        // eslint-disable-next-line prefer-const
        blen = b.length,
        // eslint-disable-next-line prefer-const
        row = Array(alen);
    for (i = 0; i <= alen; i++) {
        row[i] = i;
    }

    for (i = 1; i <= blen; i++) {
        res = i;
        for (j = 1; j <= alen; j++) {
            tmp = row[j - 1];
            row[j - 1] = res;
            res =
                b[i - 1] === a[j - 1]
                    ? tmp
                    : Math.min(tmp + 1, Math.min(res + 1, row[j] + 1));
        }
    }
    return res;
}

function funkyFactor(s1: string, s2: string) {
    if (s1.length < 3 || s2.length < 3) {
        return dziemba_levenshtein(s1, s2);
    }
    return (
        dziemba_levenshtein(s1.slice(0, 3), s2.slice(0, 3)) +
        dziemba_levenshtein(s1.slice(-3), s2.slice(-3))
    );
}

function randomOfFunky(basis: string, ary: string[]) {
    const options: { option: string; score: number }[] = [];
    for (let i = 0; i < Math.floor(ary.length / 10); i++) {
        const option = randomOf(ary);
        options.push({
            option: option,
            score: funkyFactor(basis, option),
        });
    }
    options.sort((a, b) => {
        return a.score < b.score ? -1 : 1;
    });
    return options[0].option;
}

export function randomGameName() {
    const synonym = randomOf(conflictSynonyms);
    const adjective = randomOfFunky(synonym, adjectives);
    const noun = randomOfFunky(adjective, nouns);
    return (
        "The " +
        capitalize(synonym) +
        " of the " +
        capitalize(adjective) +
        " " +
        capitalize(noun)
    );
}

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

type Order = ReturnType<typeof orderSlice.selectors.selectOrder>;

const getStepLabel = (step: string, order: Order) => {
    if (step === "source") {
        return "Select unit to order";
    }
    if (step === "type") {
        return "Select order type";
    }
    if (step === "aux") {
        return `Select unit to ${order.type}`;
    }
    if (step === "target") {
        return "Select destination";
    }
    throw new Error(`Unknown step: ${step}`);
}

const getOptions = (order: Order, options: Record<string, any>, variant: Variant) => {
    // If no source selected yet, return all top level provinces
    if (!order.source) {
        return Object.keys(options)
            .map(id => ({
                key: id,
                label: variant.provinces.find(p => p.id === id)?.name || id
            }))
            .sort((a, b) => a.label.localeCompare(b.label));
    }

    // Start at the source province node
    let node = options[order.source];
    if (!node) return [];

    // Move to Next
    node = node.Next;
    if (!node) return [];

    // If no type selected yet, return order types
    if (!order.type) {
        return Object.keys(node)
            .map(type => ({
                key: type,
                label: type
            }))
            .sort((a, b) => a.key.localeCompare(b.key));
    }

    // Move to type node
    node = node[order.type];
    if (!node) return [];

    // Move to Next
    node = node.Next;
    if (!node) return [];

    // Skip the SrcProvince level by moving to its Next
    if (node[order.source]?.Type === "SrcProvince") {
        node = node[order.source].Next;
        if (!node) return [];
    }

    // For Move orders, if target is already selected, return empty array
    if (order.type === "Move" && order.target) {
        return [];
    }

    // For Support orders, if both aux and target are selected, return empty array
    if (order.type === "Support" && order.aux && order.target) {
        return [];
    }

    // If no aux selected yet and we have aux options, return those
    if (!order.aux && Object.keys(node).length > 0 && node[Object.keys(node)[0]].Type === "Province") {
        return Object.keys(node)
            .map(id => ({
                key: id,
                label: variant.provinces.find(p => p.id === id)?.name || id
            }))
            .sort((a, b) => a.label.localeCompare(b.label));
    }

    // If aux is selected, move to aux node
    if (order.aux) {
        node = node[order.aux];
        if (!node) return [];
        node = node.Next;
        if (!node) return [];
    }

    // Return target provinces if available
    return Object.keys(node)
        .map(id => ({
            key: id,
            label: variant.provinces.find(p => p.id === id)?.name || id
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
}

const getProvince = (id: string, variant: Variant, phase: Phase): {
    id: string;
    name: string;
    unitType?: string;
} => {
    const province = variant.provinces.find((p) => p.id === id)
    if (!province) throw new Error(`Province not found: ${id}`);

    const unitType = phase.units.find((u) => u.province.id === id)?.type;
    return {
        id: province.id,
        name: province.name,
        unitType: unitType ? capitalize(unitType) : undefined,
    };
}

const getOrderSummary = (order: Order, variant: Variant, phase: Phase) => {
    const source = order.source ? getProvince(order.source, variant, phase) : undefined;
    const target = order.target ? getProvince(order.target, variant, phase) : undefined;
    const aux = order.aux ? getProvince(order.aux, variant, phase) : undefined;

    if (!source) return "";

    if (!order.type) {
        return `${source.unitType} ${source.name}...`;
    }

    if (order.type === "Hold") {
        return `${source.unitType} ${source.name} Hold`;
    }

    if (order.type === "Move") {
        if (!target) {
            return `${source.unitType} ${source.name} Move to...`;
        } else {
            return `${source.unitType} ${source.name} Move to ${target.name}`;
        }
    }

    if (order.type === "Support") {
        if (!aux) {
            return `${source.unitType} ${source.name} Support...`;
        } else if (!target) {
            return `${source.unitType} ${source.name} Support ${aux.name} to...`;
        } else {
            return `${source.unitType} ${source.name} Support ${aux.name} to ${target.name}`;
        }
    }

    if (order.type === "Convoy") {
        if (!aux) {
            return `${source.unitType} ${source.name} Convoy...`;
        } else if (!target) {
            return `${source.unitType} ${source.name} Convoy ${aux.name} to...`;
        } else {
            return `${source.unitType} ${source.name} Convoy ${aux.name} to ${target.name}`;
        }
    }

    throw new Error(`Unknown order type: ${order.type}`);

}

export { formatOrderText, transformResolution, getStepLabel, getOrderSummary, getOptions, getProvince, getCurrentPhase };