import { CssParser } from "./parsers/util/css-parser";
import { PathConverterFactory } from "./parsers/components/converter";
import { FilterFactory } from "./parsers/components/filter";
import { IdNormalizer, PathConverterNormalizer } from "./parsers/components/normalizer";
import { SelectorFactory } from "./parsers/components/selector";
import { CenterSerializer, PathSerializer, TextSerializer } from "./parsers/components/serializer";
import { Parser } from "./parsers/parser";
import { CenterParser } from "./parsers/util/center-parser";
import { StyleParser } from "./parsers/util/style-parser";
import { IMap } from "./types";
import { JSDOM } from "jsdom";

interface IMapProcessor {
    process(svg: string, idMap: Record<string, string>): IMap;
}

class MapProcessor implements IMapProcessor {
    public process(svg: string, idMap: Record<string, string>): IMap {
        console.log("Processing map...");

        const dom = new JSDOM(svg, { contentType: "image/svg+xml" });

        const svgElement = dom.window.document.querySelector("svg");
        if (!svgElement) {
            throw new Error("No SVG element found in the provided content");
        }

        // Get the dimensions from the viewbox attribute
        const viewbox = svgElement.getAttribute("viewBox");
        if (!viewbox) {
            throw new Error("No viewbox attribute found in the SVG element");
        }
        const [_, __, width, height] = viewbox.split(" ").map(parseFloat);
        console.log(`Map dimensions: ${width}x${height}`);

        const cssParser = new CssParser();
        const styleParser = new StyleParser(cssParser);
        const centerParser = new CenterParser();

        const selectorFactory = new SelectorFactory();
        const filterFactory = new FilterFactory();

        const document = dom.window.document;
        const pathConverterFactory = new PathConverterFactory(document);

        const pathConverterNormalizer = new PathConverterNormalizer(pathConverterFactory);
        const centerIdNormalizer = new IdNormalizer((id: string) => id.replace(/Center$/, ""));
        const textIdNormalizer = new IdNormalizer((id: string) => {
            return idMap[id] || id;
        });

        const pathSerializer = new PathSerializer(styleParser);
        const centerSerializer = new CenterSerializer(centerParser);
        const textSerializer = new TextSerializer(styleParser);

        console.log("Processing background elements...");
        const backgroundElements = new Parser(
            selectorFactory.create("#background path, #background polygon, #background polyline, #background rect"),
            [],
            [pathConverterNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${backgroundElements.length} background elements`);

        console.log("Processing borders...");
        const borders = new Parser(
            selectorFactory.create("#foreground path, #foreground polygon, #foreground polyline, #foreground line"),
            [filterFactory.create((elements) => elements.filter(element => !element.getAttribute("style")?.includes("url(#impassableStripes)")))],
            [pathConverterNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${borders.length} borders`);

        console.log("Processing impassable provinces...");
        const impassableProvinces = new Parser(
            selectorFactory.create("#foreground path, #foreground polygon, #foreground polyline"),
            [filterFactory.create((elements) => elements.filter(element => element.getAttribute("style")?.includes("url(#impassableStripes)")))],
            [pathConverterNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${impassableProvinces.length} impassable provinces`);

        console.log("Processing province centers...");
        const provinceCenters = new Parser(
            selectorFactory.create("#province-centers path, #province-centers polygon, #province-centers polyline"),
            [],
            [pathConverterNormalizer, centerIdNormalizer],
            centerSerializer
        ).parse(svgElement);
        console.log(`Found ${provinceCenters.length} province centers`);

        console.log("Processing supply centers...");
        const supplyCenters = new Parser(
            selectorFactory.create("#supply-centers path, #supply-centers polygon, #supply-centers polyline"),
            [],
            [pathConverterNormalizer, centerIdNormalizer],
            centerSerializer
        ).parse(svgElement);
        console.log(`Found ${supplyCenters.length} supply centers`);

        console.log("Processing names...");
        const names = new Parser(
            selectorFactory.create("#names text"),
            [],
            [textIdNormalizer],
            textSerializer
        ).parse(svgElement);

        console.log("Processing provinces...");
        const provinces = new Parser(
            selectorFactory.create("#provinces path, #provinces polygon, #provinces polyline"),
            [],
            [pathConverterNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${provinces.length} provinces`);

        const mergedProvinces = provinces.map(province => {
            const id = province.id as string;
            const provinceCenter = provinceCenters.find(center => center.id === id);
            const supplyCenter = supplyCenters.find(center => center.id === id);
            const text = names.filter(name => name.id === id);

            const center = supplyCenter || provinceCenter;
            if (!center) {
                throw new Error(`No center found for province ${id}`);
            }

            return {
                id,
                path: {
                    d: province.d,
                    styles: province.styles,
                },
                styles: province.styles,
                supplyCenter: supplyCenter?.center,
                center: center.center,
                text,
            }
        });

        return {
            width,
            height,
            provinces: mergedProvinces,
            backgroundElements,
            borders,
            impassableProvinces,
        }
    }
}

export { IMapProcessor, MapProcessor }