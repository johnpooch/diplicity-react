import { getClosestPointOnLine } from "../InteractiveMap.utils";

type ConvoyArrowProps = {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    x3: number;
    y3: number;
    lineWidth: number;
    arrowWidth: number;
    arrowLength: number;
    offset: number;
    fill: string;
    stroke: string;
    strokeWidth: number;
    dash?: { length: number; spacing: number };
    onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

const ConvoyArrow = (props: ConvoyArrowProps) => {

    // Get the closest point on the line from (x1, y1) to the line defined by (x2, y2) -> (x3, y3)
    const closestPoint = getClosestPointOnLine(
        props.x1,
        props.y1,
        props.x2,
        props.y2,
        props.x3,
        props.y3,
    );

    // Calculate the direction vector from (x1, y1) to the closest point
    const directionX = closestPoint.x - props.x1;
    const directionY = closestPoint.y - props.y1;

    // Normalize the direction vector
    const magnitude = Math.sqrt(
        directionX * directionX + directionY * directionY,
    );
    const unitX = directionX / magnitude;
    const unitY = directionY / magnitude;

    // Apply the offset in the direction of the unit vector
    const offsetX = props.offset * unitX;
    const offsetY = props.offset * unitY;

    // Adjust the start and end points by the offset
    const startX = props.x1 + offsetX;
    const startY = props.y1 + offsetY;
    const endX = closestPoint.x;
    const endY = closestPoint.y;

    const angle = Math.atan2(endY - startY, endX - startX);

    const centerX = (startX + endX) / 2;
    const centerY = (startY + endY) / 2;

    return (
        <g>
            <path
                d={`M ${startX} ${startY} L ${endX} ${endY}`}
                stroke={props.stroke}
                strokeWidth={props.lineWidth + props.strokeWidth * 2}
                strokeDasharray={
                    props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
                }
            />
            <path
                d={`M ${startX} ${startY} L ${endX} ${endY}`}
                stroke={props.fill}
                strokeWidth={props.lineWidth}
                strokeDasharray={
                    props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
                }
            />
            {props.onRenderCenter && props.onRenderCenter(centerX, centerY, angle)}
            <circle
                cx={endX}
                cy={endY}
                r={5} // Radius of the circle, can adjust this value
                fill={"white"}
                stroke={"black"}
                strokeWidth={props.strokeWidth}
            />
        </g>
    );
};

export { ConvoyArrow };