import { CSSProperties } from "react";

// LSP TEST: This should show a type error - assigning number to string
const lspTestError: string = 123;

interface IPoint {
    x: number;
    y: number;
}

interface IStyles {
    fill?: string;
    stroke?: string;
    strokeWidth?: string;
    strokeDasharray?: string;
    strokeDashoffset?: string;
    strokeOpacity?: string;
    fillOpacity?: string;
    strokeMiterlimit?: string;
    fontSize?: string;
    fontFamily?: string;
    fontWeight?: string;
    fontStyle?: string;
    letterSpacing?: string;
    transform?: string;
}

type ICenter = {
    id: string;
    center: IPoint;
}

interface IText {
    id: string;
    value: string;
    styles: IStyles;
    point: IPoint;
    transform?: string;
}

type IPath = {
    d: string;
    styles: IStyles;
    id?: string;
};

interface IProvince {
    id: string;
    center: IPoint;
    supplyCenter: IPoint | undefined;
    text: IText[] | undefined;
    path: IPath;
    transform?: string;
}

interface IMap {
    width: number;
    height: number;
    provinces: IProvince[];
    backgroundElements: IPath[];
    borders: IPath[];
    impassableProvinces: IPath[];
}

export { IMap, IPath, IPoint, IStyles, ICenter, IProvince, IText }
