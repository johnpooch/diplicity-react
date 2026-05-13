import { CssParser } from "./parsers/util/css-parser";
import { PathConverterFactory } from "./parsers/components/converter";
import { FilterFactory } from "./parsers/components/filter";
import { IdNormalizer, PathConverterNormalizer, TransformNormalizer } from "./parsers/components/normalizer";
import { SelectorFactory } from "./parsers/components/selector";
import { CenterSerializer, PathSerializer, TextSerializer } from "./parsers/components/serializer";
import { Parser } from "./parsers/parser";
import { CenterParser } from "./parsers/util/center-parser";
import { StyleParser } from "./parsers/util/style-parser";
import { parseMatrix, applyMatrixToPath } from "./parsers/util/path-transform";
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
        const transformNormalizer = new TransformNormalizer();
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
            [pathConverterNormalizer, transformNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${backgroundElements.length} background elements`);

        console.log("Processing borders...");
        const borders = new Parser(
            selectorFactory.create("#foreground path, #foreground polygon, #foreground polyline, #foreground line"),
            [filterFactory.create((elements) => elements.filter(element => !element.getAttribute("style")?.includes("url(#impassableStripes")))],
            [pathConverterNormalizer, transformNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${borders.length} borders`);

        console.log("Processing impassable provinces...");
        const impassableProvinces = new Parser(
            selectorFactory.create("#foreground path, #foreground polygon, #foreground polyline"),
            [filterFactory.create((elements) => elements.filter(element => element.getAttribute("style")?.includes("url(#impassableStripes")))],
            [pathConverterNormalizer, transformNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${impassableProvinces.length} impassable provinces`);

        console.log("Processing province centers...");
        const provinceCenters = new Parser(
            selectorFactory.create("#province-centers path, #province-centers polygon, #province-centers polyline"),
            [],
            [pathConverterNormalizer, transformNormalizer, centerIdNormalizer],
            centerSerializer
        ).parse(svgElement);
        console.log(`Found ${provinceCenters.length} province centers`);

        console.log("Processing supply centers...");
        const supplyCenters = new Parser(
            selectorFactory.create("#supply-centers path, #supply-centers polygon, #supply-centers polyline"),
            [],
            [pathConverterNormalizer, transformNormalizer, centerIdNormalizer],
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

        console.log("Processing names layer elements...");
        const namesGroup = svgElement.querySelector("#names");
        const namesTransform = namesGroup?.getAttribute("transform") || undefined;
        const namesElements = new Parser(
            selectorFactory.create("#names rect, #names path, #names polygon, #names polyline"),
            [],
            [pathConverterNormalizer],
            pathSerializer
        ).parse(svgElement);
        console.log(`Found ${namesElements.length} names layer elements`);

        // Identify supply-center star paths by their distinctive -4.908 fingerprint,
        // bake the namesLayer group transform into their coordinates, and match each
        // star to the nearest supply-center province.
        const starByProvinceId = new Map<string, string>();
        const starIndices = new Set<number>();

        const groupMatrix = namesTransform ? parseMatrix(namesTransform) : null;
        if (groupMatrix) {
            const getAnchor = (d: string) => {
                const m = /^[Mm]\s*([\d.eE+-]+)[,\s]+([\d.eE+-]+)/.exec(d.trim());
                if (!m) return null;
                const xl = parseFloat(m[1]);
                const yl = parseFloat(m[2]);
                return {
                    x: groupMatrix.a * xl + groupMatrix.e,
                    y: groupMatrix.d * yl + groupMatrix.f,
                };
            };

            const starCandidates = namesElements
                .map((el, idx) => ({ el, idx, anchor: getAnchor(el.d) }))
                .filter(({ el, anchor }) => anchor && /-4\.908/.test(el.d));

            console.log(`Found ${starCandidates.length} star candidates`);

            const usedCandidates = new Set<number>();
            for (const sc of supplyCenters) {
                let minDist = Infinity;
                let bestCandIdx = -1;
                for (let ci = 0; ci < starCandidates.length; ci++) {
                    if (usedCandidates.has(ci)) continue;
                    const anchor = starCandidates[ci].anchor!;
                    const dx = anchor.x - sc.center.x;
                    const dy = anchor.y - sc.center.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < minDist) { minDist = dist; bestCandIdx = ci; }
                }
                if (bestCandIdx >= 0) {
                    usedCandidates.add(bestCandIdx);
                    const { el, idx } = starCandidates[bestCandIdx];
                    starIndices.add(idx);
                    starByProvinceId.set(sc.id, applyMatrixToPath(el.d, groupMatrix));
                }
            }
            console.log(`Matched ${starByProvinceId.size} stars to supply centers`);
        }

        const labelElements = namesElements.filter((_, idx) => !starIndices.has(idx));

        console.log("Processing provinces...");
        const provinces = new Parser(
            selectorFactory.create("#provinces path, #provinces polygon, #provinces polyline"),
            [],
            [pathConverterNormalizer, transformNormalizer],
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
                supplyCenter: supplyCenter ? {
                    ...supplyCenter.center,
                    path: starByProvinceId.get(id),
                } : undefined,
                center: center.center,
                text,
            }
        });

        // Collect SVG filter defs referenced by background elements
        const referencedFilterIds = new Set<string>();
        for (const el of backgroundElements) {
            const filterMatch = el.styles.filter?.match(/url\(#([^)]+)\)/);
            if (filterMatch) referencedFilterIds.add(filterMatch[1]);
        }
        let svgDefs: string | undefined;
        if (referencedFilterIds.size > 0) {
            const defsEl = svgElement.querySelector("defs");
            const parts: string[] = [];
            for (const id of referencedFilterIds) {
                const filterEl = defsEl?.querySelector(`#${id}`);
                if (filterEl) parts.push(filterEl.outerHTML);
            }
            if (parts.length > 0) svgDefs = parts.join("\n");
        }

        return {
            width,
            height,
            provinces: mergedProvinces,
            backgroundElements,
            borders,
            impassableProvinces,
            namesLayer: labelElements.length > 0
                ? { transform: namesTransform, elements: labelElements }
                : undefined,
            svgDefs,
        }
    }
}

export { IMapProcessor, MapProcessor }