import { DOMParser, XMLSerializer } from "xmldom";
import { contrastColors } from "./contrast";
import { Phase } from "../schema";
import { service } from "../store";
import { IMapEditor } from "./map.types";

type Variant = typeof service.endpoints.listVariants.Types.ResultType[number];

export const getNationColor = (
    variant: Variant,
    nation: string
): string => {
    const nationColors = variant.NationColors;
    const nationColor = nationColors ? nationColors[nation] : null;
    if (nationColor) return nationColor;
    const nationNotInVariant = !variant.Nations.includes(nation);
    if (nationNotInVariant) {
        if (nation === "Neutral") {
            return "#d0d0d0";
        }
        if (nation === "Diplicity") {
            return "#000000";
        }
        throw Error(
            `Cannot find nation color for ${nation} in variant ${variant.Nations}`
        );
    }
    const index = variant.Nations.indexOf(nation);
    return contrastColors[index];
};

export interface MapState {
    provinces: {
        id: string;
        fill: string;
        highlight: boolean;
    }[];
    units: {
        fill: string;
        province: string;
        type: string;
    }[];
    orders: {
        type: string;
        source: string;
        target: string;
        aux: string;
        fill: string;
        result: string;
    }[];
}

const convertCssStringToObject = (css: string) => {
    const regex = /([\w-]*)\s*:\s*([^;]*)/g;
    let match;
    const properties: Record<string, string> = {};
    while ((match = regex.exec(css))) {
        properties[match[1]] = match[2].trim();
    }
    return properties;
};

const convertStyleObjectToCssString = (style: Record<string, string>) => {
    return Object.keys(style)
        .map((key) => `${key}: ${style[key]}`)
        .join(";");
};


const createMapState = (
    phase: Phase
) => ({
    provinces: phase.SCs.map(({ Province, Owner }) => ({
        id: Province,
        nation: Owner,
    })),
    units: phase.Units.map(({ Province, Unit }) => ({
        province: Province,
        nation: Unit.Nation,
        type: Unit.Type,
    })),
    orders: [],
});

export const createMap = (
    mapXml: string,
    armyXml: string,
    fleetXml: string,
    variant: Variant,
    phase: Phase
): string => {
    const mapEditor = new MapEditor(mapXml, armyXml, fleetXml, (nation) => getNationColor(variant, nation));
    const mapState = createMapState(phase);

    mapState.provinces.forEach(({ id, nation }) => {
        mapEditor.setOwner(id, nation);
    });

    mapState.units.forEach(({ province, nation, type }) => {
        if (type === "Army") {
            mapEditor.addArmy(province, nation);
        } else if (type === "Fleet") {
            mapEditor.addFleet(province, nation);
        } else {
            throw new Error(`Invalid type: ${type}`);
        }
    });

    return mapEditor.toString();
};

class MapEditor implements IMapEditor {

    private static readonly PROVINCE_OPACITY = "0.6";

    private static readonly UNIT_OPACITY = "1";
    private static readonly UNIT_STROKE = "#000000";
    private static readonly UNIT_STROKE_WIDTH = "3";

    private static readonly ARMY_X_OFFSET = 35;
    private static readonly ARMY_Y_OFFSET = 25;
    private static readonly FLEET_X_OFFSET = 65;
    private static readonly FLEET_Y_OFFSET = 25;

    private readonly mapSvg: SVGSVGElement;
    private readonly armySvg: SVGSVGElement;
    private readonly fleetSvg: SVGSVGElement;

    private readonly colorProvider: (nation: string) => string;

    private readonly provinceMap: Map<string, HTMLElement>;
    private readonly provinceCenterMap: Map<string, HTMLElement>;
    private readonly supplyCenterMap: Map<string, HTMLElement>;

    private readonly unitsLayer: HTMLElement;

    constructor(map: string, army: string, fleet: string, colorProvider: (nation: string) => string) {

        const parser = new DOMParser();

        this.mapSvg = this.parseSvg(parser, map);
        this.armySvg = this.parseSvg(parser, army);
        this.fleetSvg = this.parseSvg(parser, fleet);

        this.colorProvider = colorProvider;


        this.unitsLayer = this.mapSvg.ownerDocument.getElementById("units") as HTMLElement;

        const provincesLayer = this.mapSvg.ownerDocument.getElementById("provinces") as HTMLElement;
        const provinceCentersLayer = this.mapSvg.ownerDocument.getElementById("province-centers") as HTMLElement;
        const supplyCentersLayer = this.mapSvg.ownerDocument.getElementById("supply-centers") as HTMLElement;

        this.provinceMap = new Map();
        this.provinceCenterMap = new Map();
        this.supplyCenterMap = new Map();

        Object.values(provincesLayer.childNodes).filter(this.isHtmlElement).forEach((el) => {
            const id = el.getAttribute("id");
            if (!id) throw new Error("Province has no id");
            el.setAttribute("style", "fill:transparent");
            this.provinceMap.set(id, el);
        });
        Object.values(provinceCentersLayer.childNodes).filter(this.isHtmlElement).forEach((el) => {
            const id = el.getAttribute("id");
            if (!id) throw new Error("Province center has no id");
            this.provinceCenterMap.set(this.removeSuffix(id, "Center"), el);
        });
        Object.values(supplyCentersLayer.childNodes).filter(this.isHtmlElement).forEach((el) => {
            const id = el.getAttribute("id");
            if (!id) throw new Error("Supply center has no id");
            this.supplyCenterMap.set(this.removeSuffix(id, "Center"), el);
        });

        provincesLayer.setAttribute("style", "")
    }

    public setOwner(name: string, nation: string): void {
        const province = this.getProvince(name);
        this.updateStyle(province, { fill: this.colorProvider(nation) });
        this.updateStyle(province, { "fill-opacity": MapEditor.PROVINCE_OPACITY });
    }

    public addArmy(province: string, nation: string): void {
        this.addUnit(province, nation, "Army");
    }

    public addFleet(province: string, nation: string): void {
        this.addUnit(province, nation, "Fleet");
    }

    public toString(): string {
        const serializer = new XMLSerializer();
        return serializer.serializeToString(this.mapSvg);
    }

    private updateStyle(element: HTMLElement, style: Record<string, string>) {
        const currentStyle = convertCssStringToObject(element.getAttribute("style") || "");
        element.setAttribute("style", convertStyleObjectToCssString({ ...currentStyle, ...style }));
    }

    private getUnitShape(type: string) {
        const shape = type === "Army" ? this.armySvg.ownerDocument.getElementById("body")?.getAttribute("d") : this.fleetSvg.ownerDocument.getElementById("hull")?.getAttribute("d");
        if (!shape) throw new Error(`${type} shape not found`);
        return shape;
    }

    private addUnit(province: string, nation: string, type: "Army" | "Fleet") {
        const [x, y] = this.getProvinceCenter(province);
        const fill = this.colorProvider(nation);

        const shape = this.getUnitShape(type);

        const path = this.unitsLayer.ownerDocument.createElement("path");

        this.updateStyle(path, { fill });
        this.updateStyle(path, { "fill-opacity": MapEditor.UNIT_OPACITY });
        this.updateStyle(path, { stroke: MapEditor.UNIT_STROKE });
        this.updateStyle(path, { "stroke-width": MapEditor.UNIT_STROKE_WIDTH });

        path.setAttribute("d", shape);
        path.setAttribute("transform", `translate(${x - (type === "Army" ? MapEditor.ARMY_X_OFFSET : MapEditor.FLEET_X_OFFSET)},${y - (type === "Army" ? MapEditor.ARMY_Y_OFFSET : MapEditor.FLEET_Y_OFFSET)})`);

        this.unitsLayer.appendChild(path);
    }

    private getProvince(name: string) {
        const province = this.provinceMap.get(name);
        if (!province) throw new Error(`Province ${name} not found`);
        return province;
    }

    private getProvinceCenter(name: string) {
        const provinceCenter = this.provinceCenterMap.get(name);
        if (provinceCenter) {
            return this.parseDCenter(provinceCenter, name);
        }
        const supplyCenter = this.supplyCenterMap.get(name);
        if (supplyCenter) {
            return this.parseDCenter(supplyCenter, name);
        }
        throw new Error(`No supply center or province center for province ${name}`);
    }

    private removeSuffix(value: string, suffix: string) {
        return value.substring(0, value.lastIndexOf(suffix));
    }

    private isHtmlElement(element: ChildNode): element is HTMLElement {
        return element.nodeType === 1;
    }

    private parseSvg(parser: DOMParser, svgString: string): SVGSVGElement {
        return parser.parseFromString(svgString, "image/svg+xml").getElementsByTagName("svg")[0];
    }

    private parseDCenter(element: HTMLElement, name: string): [number, number] {
        const d = element.getAttribute("d");
        if (!d) throw new Error(`${name} has no d attribute`);
        const match = /^m\s+([\d-.]+),([\d-.]+)\s+/.exec(d);
        if (!match) throw new Error(`Invalid d attribute: ${d}`);
        return [Number(match[1]), Number(match[2])];
    }
}