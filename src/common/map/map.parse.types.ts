import { CSSProperties } from "react";

type Point = {
    x: number;
    y: number;
}

type Path = string;

type TextStyles = Pick<CSSProperties, 'fontSize' | 'fontFamily' | 'fontWeight' | 'transform'>;

type PathStyles = Pick<CSSProperties, 'fill' | 'stroke' | 'strokeWidth' | 'strokeLinecap' | 'strokeLinejoin' | 'strokeDasharray' | 'strokeDashoffset' | 'strokeOpacity' | 'fillOpacity' | 'strokeMiterlimit'>;

type Text = {
    value: string;
    styles: TextStyles;
    point: Point;
}

type Province = {
    id: string;
    center: Point;
    supplyCenter: boolean;
    text: Text | undefined;
    path: string;
    transform?: string;
}

type ImpassableProvince = {
    path: string;
}

type Border = {
    path: string;
}


type BackgroundElement = {
    path: Path;
    styles: PathStyles;
}

type Map = {
    height: number;
    width: number;
    backgroundElements: BackgroundElement[];
    borders: Border[];
    provinces: Province[];
    impassableProvinces: ImpassableProvince[];
}

export type { Map, Point, Text, PathStyles }