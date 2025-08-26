import { describe, test, expect } from 'vitest';
import {
    HasBackgroundLayerValidator,
    HasForegroundLayerValidator,
    HasSupplyCentersLayerValidator,
    HasProvinceCentersLayerValidator,
    HasNamesLayerValidator,
    HasProvincesLayerValidator
} from '../validator';

const createRoot = (svg: string) => {
    const document = new DOMParser().parseFromString(svg, "image/svg+xml");
    return document.documentElement;
}

describe('HasBackgroundLayerValidator', () => {
    const validator = new HasBackgroundLayerValidator();

    test('should validate when background layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="background">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when background layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element background not found');
    });
});

describe('HasProvincesLayerValidator', () => {
    const validator = new HasProvincesLayerValidator();

    test('should validate when provinces layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="provinces">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when provinces layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element provinces not found');
    });
});

describe('HasSupplyCentersLayerValidator', () => {
    const validator = new HasSupplyCentersLayerValidator();

    test('should validate when supply-centers layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="supply-centers">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when supply-centers layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element supply-centers not found');
    });
});

describe('HasProvinceCentersLayerValidator', () => {
    const validator = new HasProvinceCentersLayerValidator();

    test('should validate when province-centers layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="province-centers">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when province-centers layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element province-centers not found');
    });
});

describe('HasForegroundLayerValidator', () => {
    const validator = new HasForegroundLayerValidator();

    test('should validate when foreground layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="foreground">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when foreground layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element foreground not found');
    });
});

describe('HasNamesLayerValidator', () => {
    const validator = new HasNamesLayerValidator();

    test('should validate when names layer exists', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
                <g id="names">
                </g>
            </svg>
        `);
        expect(validator.validate(root)).toBe(true);
    });

    test('should throw error when names layer is missing', () => {
        const root = createRoot(`
            <svg xmlns="http://www.w3.org/2000/svg">
            </svg>
        `);
        expect(() => validator.validate(root)).toThrow('Element names not found');
    });
});