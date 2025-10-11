type MinusProps = {
    x: number;
    y: number;
    width: number;
    length: number;
    angle: number;
    fill: string;
    stroke: string;
    strokeWidth: number;
};

const Minus = (props: MinusProps) => {
    const halfLength = props.length / 2;
    const strokeWidth = props.strokeWidth;

    const x3 = props.x;
    const y3 = props.y - halfLength;
    const x4 = props.x;
    const y4 = props.y + halfLength;

    const fillY3 = y3 + strokeWidth;
    const fillY4 = y4 - strokeWidth;

    return (
        <g transform={`rotate(${props.angle}, ${props.x}, ${props.y})`}>
            <g>
                <line
                    x1={x3}
                    y1={y3}
                    x2={x4}
                    y2={y4}
                    stroke={props.stroke}
                    strokeWidth={props.width + props.strokeWidth * 2}
                />
            </g>
            <g>
                <line
                    x1={x3}
                    y1={fillY3}
                    x2={x4}
                    y2={fillY4}
                    stroke={props.fill}
                    strokeWidth={props.width}
                />
            </g>
        </g>
    );
};

export { Minus };
