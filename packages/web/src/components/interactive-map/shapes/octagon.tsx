type OctagonProps = {
  x: number;
  y: number;
  size: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  onRenderBottomCenter?: (x: number, y: number) => React.ReactElement;
};

const Octagon = (props: OctagonProps) => {
  const angle = Math.PI / 4;
  const radius = props.size / (2 * Math.sin(angle));
  const points = Array.from({ length: 8 }).map((_, i) => {
    const theta = angle * i + Math.PI / 8; // Rotate by 22.5 degrees
    return [
      props.x + radius * Math.cos(theta),
      props.y + radius * Math.sin(theta),
    ].join(",");
  });

  const bottomCenterX =
    (parseFloat(points[1].split(",")[0]) +
      parseFloat(points[2].split(",")[0])) /
    2;
  const bottomCenterY =
    (parseFloat(points[1].split(",")[1]) +
      parseFloat(points[2].split(",")[1])) /
    2;

  return (
    <g>
      <polygon
        points={points.join(" ")}
        fill={props.fill}
        stroke={props.stroke}
        strokeWidth={props.strokeWidth}
      />
      {props.onRenderBottomCenter &&
        props.onRenderBottomCenter(bottomCenterX, bottomCenterY)}
    </g>
  );
};

export { Octagon };
