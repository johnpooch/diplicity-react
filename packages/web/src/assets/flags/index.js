import ClassicalEngland from "./classical/england.svg";
import ClassicalFrance from "./classical/france.svg";
import ClassicalGermany from "./classical/germany.svg";
import ClassicalItaly from "./classical/italy.svg";
import ClassicalAustria from "./classical/austria.svg";
import ClassicalTurkey from "./classical/turkey.svg";
import ClassicalRussia from "./classical/russia.svg";

const Flags = {
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