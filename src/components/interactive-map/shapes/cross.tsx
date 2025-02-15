type CrossProps = {
  x: number;
  y: number;
  width: number;
  length: number;
  angle: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
};

const Cross = (props: CrossProps) => {
  const halfLength = props.length / 2;
  const strokeWidth = props.strokeWidth;

  const x1 = props.x - halfLength;
  const y1 = props.y;
  const x2 = props.x + halfLength;
  const y2 = props.y;

  const x3 = props.x;
  const y3 = props.y - halfLength;
  const x4 = props.x;
  const y4 = props.y + halfLength;

  const fillX1 = x1 + strokeWidth;
  const fillX2 = x2 - strokeWidth;
  const fillY3 = y3 + strokeWidth;
  const fillY4 = y4 - strokeWidth;

  return (
    <g transform={`rotate(${props.angle}, ${props.x}, ${props.y})`}>
      <g>
        {/* Stroke */}
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={props.stroke}
          strokeWidth={props.width + props.strokeWidth * 2}
        />
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
        {/* Fill */}
        <line
          x1={fillX1}
          y1={y1}
          x2={fillX2}
          y2={y2}
          stroke={props.fill}
          strokeWidth={props.width}
        />
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

export { Cross };
