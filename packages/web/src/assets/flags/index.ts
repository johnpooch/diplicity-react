import ClassicalEngland from "./classical/england.svg";
import ClassicalFrance from "./classical/france.svg";
import ClassicalGermany from "./classical/germany.svg";
import ClassicalItaly from "./classical/italy.svg";
import ClassicalAustria from "./classical/austria.svg";
import ClassicalTurkey from "./classical/turkey.svg";
import ClassicalRussia from "./classical/russia.svg";

type NationFlags = {
    england?: string;
    france?: string;
    germany?: string;
    italy?: string;
    austria?: string;
    turkey?: string;
    russia?: string;
};

type FlagsType = {
    classical: NationFlags;
    "italy-vs-germany": NationFlags;
};

const Flags: FlagsType = {
    classical: {
        england: ClassicalEngland,
        france: ClassicalFrance,
        germany: ClassicalGermany,
        italy: ClassicalItaly,
        austria: ClassicalAustria,
        turkey: ClassicalTurkey,
        russia: ClassicalRussia,
    },
    ["italy-vs-germany"]: {
        germany: ClassicalGermany,
        italy: ClassicalItaly,
    },
};

export { Flags };