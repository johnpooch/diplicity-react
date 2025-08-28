import React, { useRef, useEffect, useState } from "react";
import { Skeleton } from "@mui/material";

const MapSkeleton: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number>(200);
  const aspectRatio = 1357 / 1524;

  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        const calculatedHeight = width * aspectRatio;
        setHeight(calculatedHeight);
      }
    };

    updateHeight();

    // Add resize listener
    const resizeObserver = new ResizeObserver(updateHeight);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [aspectRatio]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <Skeleton
        variant="rectangular"
        width="100%"
        height={height}
        sx={{
          maxHeight: "100%",
          minHeight: "200px", // Fallback minimum height
        }}
      />
    </div>
  );
};

export { MapSkeleton };
