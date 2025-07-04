#!/usr/bin/env node

console.log("CLI script starting...");
console.log("About to import modules...");

const startTime = Date.now();
console.log(`Current time: ${new Date(startTime).toISOString()}`);

import { MapProcessor } from "./map-processor";
import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

console.log(`Modules imported successfully, time: ${Date.now() - startTime}ms`);

function printUsage() {
    console.log(`
Usage: map-parse <svg-file> <id-map-file> [output-file]

Arguments:
  svg-file      Path to the SVG file to parse
  id-map-file   Path to the JSON file containing ID mappings
  output-file   (Optional) Path to output the parsed map JSON. If not provided, outputs to stdout

Examples:
  map-parse map.svg id-mapping.json
  map-parse map.svg id-mapping.json output.json
`);
}

function main() {
    const startTime = Date.now();
    console.log("Running...");
    const args = process.argv.slice(2);
    console.log("Args:", args);

    if (args.length < 2 || args.length > 3) {
        printUsage();
        process.exit(1);
    }

    const [svgFile, idMapFile, outputFile] = args;
    console.log("SVG file:", svgFile);
    console.log("ID map file:", idMapFile);
    console.log("Output file:", outputFile);

    try {
        console.log("Reading SVG file...");
        const fileReadStart = Date.now();
        // Read SVG file
        const svgContent = readFileSync(resolve(svgFile), 'utf-8');
        console.log(`SVG file read, length: ${svgContent.length}, time: ${Date.now() - fileReadStart}ms`);

        console.log("Reading ID mapping file...");
        const idMapReadStart = Date.now();
        // Read ID mapping file
        const idMapContent = readFileSync(resolve(idMapFile), 'utf-8');
        console.log(`ID map file read, length: ${idMapContent.length}, time: ${Date.now() - idMapReadStart}ms`);

        console.log("Parsing ID map JSON...");
        const jsonParseStart = Date.now();
        const idMap = JSON.parse(idMapContent);
        console.log(`ID map parsed, keys: ${Object.keys(idMap).length}, time: ${Date.now() - jsonParseStart}ms`);

        console.log("Parsing map...");
        const mapParseStart = Date.now();
        // Parse the map
        const parsedMap = new MapProcessor().process(svgContent, idMap);
        console.log(`Map parsed successfully, time: ${Date.now() - mapParseStart}ms`);

        // Output the result
        const stringifyStart = Date.now();
        const output = JSON.stringify(parsedMap, null, 2);
        console.log(`JSON stringified, length: ${output.length}, time: ${Date.now() - stringifyStart}ms`);

        if (outputFile) {
            console.log("Writing to output file...");
            const writeStart = Date.now();
            writeFileSync(resolve(outputFile), output, 'utf-8');
            console.log(`Map parsed successfully and saved to ${outputFile}, time: ${Date.now() - writeStart}ms`);
        } else {
            console.log("Outputting to stdout...");
            console.log(output);
        }

        console.log(`Total execution time: ${Date.now() - startTime}ms`);

    } catch (error) {
        console.error('Error:', error instanceof Error ? error.message : error);
        if (error instanceof Error && error.stack) {
            console.error('Stack:', error.stack);
        }
        process.exit(1);
    }
}

// Check if this file is being run directly
if (require.main === module) {
    main();
} 