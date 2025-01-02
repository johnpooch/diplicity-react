import { DOMParser, XMLSerializer } from "xmldom";
import { Variant } from "../store";
import { contrastColors } from "./contrast";
import { Phase } from "../schema";

interface Style {
    [key: string]: string;
}

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
    const properties: Style = {};
    while ((match = regex.exec(css))) {
        properties[match[1]] = match[2].trim();
    }
    return properties;
};

const convertStyleObjectToCssString = (style: Style) => {
    return Object.keys(style)
        .map((key) => `${key}: ${style[key]}`)
        .join(";");
};

const provinceFactory = (element: HTMLElement) => {
    return new Province(element);
};

const mapArrayToObjectById = <T extends { id: string }>(array: T[]) => {
    return array.reduce((prev, curr) => {
        prev[curr.id] = curr;
        return prev;
    }, {} as { [key: string]: T });
};

abstract class ElementEditor {
    element: Element;
    id: string;
    constructor(element: Element) {
        this.element = element;
        this.id = this.getAttribute("id");
    }
    getStyle() {
        return convertCssStringToObject(this.getAttribute("style"));
    }
    setStyle(style: Style) {
        this.element.setAttribute("style", convertStyleObjectToCssString(style));
    }
    updateStyle(style: Style) {
        this.setStyle({ ...this.getStyle(), ...style });
    }
    getAttribute(name: string) {
        const value = this.element.getAttribute(name);
        if (!value) {
            throw new Error(`Element has no attribute "${name}"`);
        }
        return value;
    }
    protected getChildren() {
        return Object.values(this.element.childNodes).filter(
            (el) => el.nodeType === 1
        ) as HTMLElement[];
    }
}

class Province extends ElementEditor {
    constructor(element: HTMLElement) {
        super(element);
        // Set all provinces to transparent on initialization.
        // By default provinces are black.
        this.fill("transparent");
    }

    fill(color: string) {
        this.updateStyle({ fill: color });
    }
}

const supplyCenterFactory = (element: Element) => {
    return new SupplyCenter(element);
};

class SupplyCenter extends ElementEditor {
    constructor(element: Element) {
        super(element);
        const fullId = this.getAttribute("id");
        this.id = fullId.substring(0, fullId.lastIndexOf("Center"));
    }
    getPosition() {
        const d = this.getAttribute("d");
        const match = /^m\s+([\d-.]+),([\d-.]+)\s+/.exec(d);
        if (!match) {
            throw new Error(`Invalid d attribute: ${d}`);
        }
        return [Number(match[1]), Number(match[2])];
    }
}

const supplyCenterLayerFactory = (element: Element) => {
    return new SupplyCenterLayer(element);
};

class SupplyCenterLayer extends ElementEditor {
    supplyCenterMap: Map<string, SupplyCenter>;
    constructor(element: Element) {
        super(element);
        this.supplyCenterMap = new Map(
            Object.entries(mapArrayToObjectById(this.createSupplyCenters()))
        );
    }
    private createSupplyCenters() {
        return this.getChildren().map(supplyCenterFactory);
    }
    show() {
        this.setStyle({});
    }
}

const provinceCenterFactory = (element: Element) => {
    return new ProvinceCenter(element);
};

class ProvinceCenter extends ElementEditor {
    constructor(element: Element) {
        super(element);
        const fullId = this.getAttribute("id");
        this.id = fullId.substring(0, fullId.lastIndexOf("Center"));
    }
    getPosition() {
        const d = this.getAttribute("d");
        const match = /^m\s+([\d-.]+),([\d-.]+)\s+/.exec(d);
        if (!match) {
            throw new Error(`Invalid d attribute: ${d}`);
        }
        return [Number(match[1]), Number(match[2])];
    }
}

const provinceCenterLayerFactory = (element: Element) => {
    return new ProvinceCenterLayer(element);
};

class ProvinceCenterLayer extends ElementEditor {
    provinceCenterMap: Map<string, ProvinceCenter>;
    constructor(element: Element) {
        super(element);
        this.provinceCenterMap = new Map(
            Object.entries(mapArrayToObjectById(this.createProvinceCenters()))
        );
    }
    private createProvinceCenters() {
        return this.getChildren().map(provinceCenterFactory);
    }
    show() {
        this.setStyle({});
    }
}

const provinceLayerFactory = (element: Element) => {
    return new ProvinceLayer(element);
};

class ProvinceLayer extends ElementEditor {
    provinceMap: Map<string, Province>;
    constructor(element: Element) {
        super(element);
        this.provinceMap = new Map(
            Object.entries(mapArrayToObjectById(this.createProvinces()))
        );
    }
    private createProvinces() {
        return this.getChildren().map(provinceFactory);
    }
    show() {
        this.setStyle({});
    }
}

const unitLayerFactory = (element: Element) => {
    return new UnitLayer(element);
};

class UnitLayer extends ElementEditor {
    addUnit(x: number, y: number, d: string, fill: string) {
        const path = this.element.ownerDocument.createElement("path");
        path.setAttribute(
            "style",
            `fill:${fill};fill-opacity:1;stroke:#000000;stroke-width:1;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none`
        );
        path.setAttribute("d", d);
        path.setAttribute("transform", `translate(${x},${y})`);
        this.element.appendChild(path);
    }
}

class MapEditor extends ElementEditor {
    armyPath: string;
    fleetPath: string;
    provinceCenterLayer: ProvinceCenterLayer;
    provinceCenterMap: ProvinceCenterLayer["provinceCenterMap"];
    provinceLayer: ProvinceLayer;
    provinceMap: ProvinceLayer["provinceMap"];
    supplyCenterLayer: SupplyCenterLayer;
    supplyCenterMap: SupplyCenterLayer["supplyCenterMap"];
    unitLayer: UnitLayer;

    constructor(element: Element, armyPath: string, fleetPath: string) {
        super(element);
        this.provinceLayer = provinceLayerFactory(
            this.getElementByIdOrError("provinces")
        );
        this.unitLayer = unitLayerFactory(this.getElementByIdOrError("units"));
        this.provinceCenterLayer = provinceCenterLayerFactory(
            this.getElementByIdOrError("province-centers")
        );
        this.supplyCenterLayer = supplyCenterLayerFactory(
            this.getElementByIdOrError("supply-centers")
        );
        this.provinceMap = this.provinceLayer.provinceMap;
        this.provinceCenterMap = this.provinceCenterLayer.provinceCenterMap;
        this.supplyCenterMap = this.supplyCenterLayer.supplyCenterMap;
        this.armyPath = armyPath;
        this.fleetPath = fleetPath;
    }
    setState(state: MapState) {
        state.provinces.forEach(({ id, fill }) => {
            this.provinceMap.get(id)?.fill(fill);
        });
        state.units.forEach(({ province, fill, type }) => {
            if (type === "Army") {
                this.addArmy(province, fill);
            } else if (type === "Fleet") {
                this.addFleet(province, fill);
            } else {
                throw new Error(`Invalid type: ${type}`);
            }
        });
        this.provinceLayer.show();
    }
    serializeToString() {
        const serializer = new XMLSerializer();
        return serializer.serializeToString(this.element);
    }
    private addArmy(provinceId: string, fill: string) {
        const [x, y] = this.getCenter(provinceId);
        this.unitLayer.addUnit(x - 35, y - 25, this.armyPath, fill);
    }
    private addFleet(provinceId: string, fill: string) {
        const [x, y] = this.getCenter(provinceId);
        this.unitLayer.addUnit(x - 65, y - 25, this.fleetPath, fill);
    }
    private getCenter(provinceId: string) {
        const provinceCenter = this.provinceCenterMap.get(provinceId);
        if (provinceCenter) {
            return provinceCenter.getPosition();
        }
        const supplyCenter = this.supplyCenterMap.get(provinceId);
        if (supplyCenter) {
            return supplyCenter.getPosition();
        }
        throw new Error(
            `No supply center or province center for province ${provinceId}`
        );
    }
    private getElementByIdOrError(id: string) {
        const element = this.element.ownerDocument.getElementById(id);
        if (!element) {
            throw new Error(`Could not find element with id ${id}`);
        }
        return element;
    }
}

const mapEditorFactory = (
    mapXml: string,
    armyXml: string,
    fleetXml: string
) => {
    const parser = new DOMParser();
    const mapDocument = parser.parseFromString(mapXml);
    const armyDocument = parser.parseFromString(armyXml);
    const fleetDocument = parser.parseFromString(fleetXml);
    const mapSvg = mapDocument.getElementsByTagName("svg")[0];
    const armyPath = armyDocument.getElementById("body")?.getAttribute("d") || "";
    const fleetPath =
        fleetDocument.getElementById("hull")?.getAttribute("d") || "";
    return new MapEditor(mapSvg, armyPath, fleetPath);
};

export const updateMap = (
    mapXml: string,
    armyXml: string,
    fleetXml: string,
    mapState: MapState
): string => {
    const mapEditor = mapEditorFactory(mapXml, armyXml, fleetXml);
    mapEditor.setState(mapState);
    return mapEditor.serializeToString();
};

const createMapState = (
    variant: Variant,
    phase: Phase
): MapState => ({
    provinces: phase.SCs.map(({ Province, Owner }) => ({
        id: Province,
        fill: getNationColor(variant, Owner),
        highlight: false,
    })),
    units: phase.Units.map(({ Province, Unit }) => ({
        province: Province,
        fill: getNationColor(variant, Unit.Nation),
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
    const mapEditor = mapEditorFactory(mapXml, armyXml, fleetXml);
    mapEditor.setState(createMapState(variant, phase));
    return mapEditor.serializeToString();
};