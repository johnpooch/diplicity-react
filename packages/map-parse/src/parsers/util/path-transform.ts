interface Matrix {
    a: number;
    b: number;
    c: number;
    d: number;
    e: number;
    f: number;
}

const parseMatrix = (transform: string): Matrix | null => {
    const m = transform.match(
        /matrix\(\s*([-\d.eE+]+)[,\s]+([-\d.eE+]+)[,\s]+([-\d.eE+]+)[,\s]+([-\d.eE+]+)[,\s]+([-\d.eE+]+)[,\s]+([-\d.eE+]+)\s*\)/
    );
    if (!m) return null;
    return {
        a: parseFloat(m[1]),
        b: parseFloat(m[2]),
        c: parseFloat(m[3]),
        d: parseFloat(m[4]),
        e: parseFloat(m[5]),
        f: parseFloat(m[6]),
    };
};

const tpt = (x: number, y: number, m: Matrix): [number, number] => [
    m.a * x + m.c * y + m.e,
    m.b * x + m.d * y + m.f,
];

const round = (n: number): string => parseFloat(n.toFixed(4)).toString();

const parseNums = (s: string): number[] => {
    const nums: number[] = [];
    const re = /[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/g;
    let match: RegExpExecArray | null;
    while ((match = re.exec(s)) !== null) {
        nums.push(parseFloat(match[0]));
    }
    return nums;
};

const tokenize = (d: string): Array<{ cmd: string; args: number[] }> => {
    const segs: Array<{ cmd: string; args: number[] }> = [];
    const re = /([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(d)) !== null) {
        segs.push({ cmd: m[1], args: parseNums(m[2]) });
    }
    return segs;
};

const applyMatrixToPath = (d: string, mx: Matrix): string => {
    let cx = 0, cy = 0;
    let sx = 0, sy = 0;
    const out: string[] = [];

    for (const { cmd, args } of tokenize(d)) {
        switch (cmd) {
            case 'M': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx = args[i]; cy = args[i + 1];
                    if (i === 0) { sx = cx; sy = cy; }
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`M ${pts.join(' ')}`);
                break;
            }
            case 'm': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx += args[i]; cy += args[i + 1];
                    if (i === 0) { sx = cx; sy = cy; }
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`M ${pts.join(' ')}`);
                break;
            }
            case 'L': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx = args[i]; cy = args[i + 1];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'l': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx += args[i]; cy += args[i + 1];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'H': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i++) {
                    cx = args[i];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'h': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i++) {
                    cx += args[i];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'V': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i++) {
                    cy = args[i];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'v': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i++) {
                    cy += args[i];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`L ${pts.join(' ')}`);
                break;
            }
            case 'C': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 6) {
                    const [x1, y1] = tpt(args[i], args[i + 1], mx);
                    const [x2, y2] = tpt(args[i + 2], args[i + 3], mx);
                    cx = args[i + 4]; cy = args[i + 5];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x1)},${round(y1)} ${round(x2)},${round(y2)} ${round(x)},${round(y)}`);
                }
                out.push(`C ${pts.join(' ')}`);
                break;
            }
            case 'c': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 6) {
                    const [x1, y1] = tpt(cx + args[i], cy + args[i + 1], mx);
                    const [x2, y2] = tpt(cx + args[i + 2], cy + args[i + 3], mx);
                    cx += args[i + 4]; cy += args[i + 5];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x1)},${round(y1)} ${round(x2)},${round(y2)} ${round(x)},${round(y)}`);
                }
                out.push(`C ${pts.join(' ')}`);
                break;
            }
            case 'S': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 4) {
                    const [x2, y2] = tpt(args[i], args[i + 1], mx);
                    cx = args[i + 2]; cy = args[i + 3];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x2)},${round(y2)} ${round(x)},${round(y)}`);
                }
                out.push(`S ${pts.join(' ')}`);
                break;
            }
            case 's': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 4) {
                    const [x2, y2] = tpt(cx + args[i], cy + args[i + 1], mx);
                    cx += args[i + 2]; cy += args[i + 3];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x2)},${round(y2)} ${round(x)},${round(y)}`);
                }
                out.push(`S ${pts.join(' ')}`);
                break;
            }
            case 'Q': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 4) {
                    const [x1, y1] = tpt(args[i], args[i + 1], mx);
                    cx = args[i + 2]; cy = args[i + 3];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x1)},${round(y1)} ${round(x)},${round(y)}`);
                }
                out.push(`Q ${pts.join(' ')}`);
                break;
            }
            case 'q': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 4) {
                    const [x1, y1] = tpt(cx + args[i], cy + args[i + 1], mx);
                    cx += args[i + 2]; cy += args[i + 3];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x1)},${round(y1)} ${round(x)},${round(y)}`);
                }
                out.push(`Q ${pts.join(' ')}`);
                break;
            }
            case 'T': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx = args[i]; cy = args[i + 1];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`T ${pts.join(' ')}`);
                break;
            }
            case 't': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 2) {
                    cx += args[i]; cy += args[i + 1];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(x)},${round(y)}`);
                }
                out.push(`T ${pts.join(' ')}`);
                break;
            }
            case 'A': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 7) {
                    const rx = Math.abs(mx.a) * args[i];
                    const ry = Math.abs(mx.d) * args[i + 1];
                    const xRot = args[i + 2];
                    const largeArc = args[i + 3];
                    const sweep = args[i + 4];
                    cx = args[i + 5]; cy = args[i + 6];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(rx)},${round(ry)} ${xRot} ${largeArc} ${sweep} ${round(x)},${round(y)}`);
                }
                out.push(`A ${pts.join(' ')}`);
                break;
            }
            case 'a': {
                const pts: string[] = [];
                for (let i = 0; i < args.length; i += 7) {
                    const rx = Math.abs(mx.a) * args[i];
                    const ry = Math.abs(mx.d) * args[i + 1];
                    const xRot = args[i + 2];
                    const largeArc = args[i + 3];
                    const sweep = args[i + 4];
                    cx += args[i + 5]; cy += args[i + 6];
                    const [x, y] = tpt(cx, cy, mx);
                    pts.push(`${round(rx)},${round(ry)} ${xRot} ${largeArc} ${sweep} ${round(x)},${round(y)}`);
                }
                out.push(`A ${pts.join(' ')}`);
                break;
            }
            case 'Z':
            case 'z':
                cx = sx; cy = sy;
                out.push('Z');
                break;
        }
    }

    return out.join(' ');
};

export { Matrix, parseMatrix, applyMatrixToPath };
