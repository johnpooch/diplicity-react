import { CSSProperties } from "react";

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
    filter?: string;
}

type ICenter = {
    id: string;
    center: IPoint;
}

interface ITspan {
    value: string;
    x: number;
    y: number;
}

interface IText {
    id: string;
    value: string;
    tspans: ITspan[];
    styles: IStyles;
    point: IPoint;
    transform?: string;
}

type IPath = {
    d: string;
    styles: IStyles;
    id?: string;
};

interface ISupplyCenter extends IPoint {
    path?: string;
}

interface IProvince {
    id: string;
    center: IPoint;
    supplyCenter: ISupplyCenter | undefined;
    text: IText[] | undefined;
    path: IPath;
    transform?: string;
}

interface INamesLayer {
    transform?: string;
    elements: IPath[];
}

interface IMap {
    width: number;
    height: number;
    provinces: IProvince[];
    backgroundElements: IPath[];
    borders: IPath[];
    impassableProvinces: IPath[];
    namesLayer?: INamesLayer;
    svgDefs?: string;
}

export { IMap, IPath, IPoint, IStyles, ICenter, IProvince, IText, ITspan, INamesLayer, ISupplyCenter }
