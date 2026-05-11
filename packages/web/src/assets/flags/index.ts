import ClassicalEngland from "./classical/england.svg";
import ClassicalFrance from "./classical/france.svg";
import ClassicalGermany from "./classical/germany.svg";
import ClassicalItaly from "./classical/italy.svg";
import ClassicalAustria from "./classical/austria.svg";
import ClassicalTurkey from "./classical/turkey.svg";
import ClassicalRussia from "./classical/russia.svg";
import VietnamWarCambodia from "./vietnam-war/cambodia.svg";
import VietnamWarLaos from "./vietnam-war/laos.svg";
import VietnamWarNorthVietnam from "./vietnam-war/north-vietnam.svg";
import VietnamWarSouthVietnam from "./vietnam-war/south-vietnam.svg";
import VietnamWarThailand from "./vietnam-war/thailand.svg";
import CantonTurkey from "./canton/turkey.svg";
import CantonBritain from "./canton/britain.svg";
import CantonChina from "./canton/china.svg";
import CantonHolland from "./canton/holland.svg";
import CantonJapan from "./canton/japan.svg";
import CantonRussia from "./canton/russia.svg";
import CantonFrance from "./canton/france.svg";

type NationFlags = Record<string, string>;

type FlagsType = Record<string, NationFlags>;

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
    ["vietnam-war"]: {
        cambodia: VietnamWarCambodia,
        laos: VietnamWarLaos,
        ["north vietnam"]: VietnamWarNorthVietnam,
        ["south vietnam"]: VietnamWarSouthVietnam,
        thailand: VietnamWarThailand,
    },
    canton: {
        turkey: CantonTurkey,
        britain: CantonBritain,
        china: CantonChina,
        holland: CantonHolland,
        japan: CantonJapan,
        russia: CantonRussia,
        france: CantonFrance,
    },
};

export { Flags };