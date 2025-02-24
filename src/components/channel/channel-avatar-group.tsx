import React from "react";
import { Avatar, Box } from "@mui/material";

interface ChannelAvatarGroupProps {
  displayNames: string[];
  variant?: {
    Flags: Record<string, string>;
  };
}

const ChannelAvatarGroup: React.FC<ChannelAvatarGroupProps> = ({ displayNames, variant }) => {
  const MAX_AVATARS = 9;
  const names = displayNames.slice(0, MAX_AVATARS);
  const count = names.length;
  
  const containerSize = 40;
  const getGridDimensions = (count: number): [number, number] => {
    if (count <= 1) return [1, 1];
    if (count === 2) return [2, 1];
    if (count <= 4) return [2, 2];
    if (count <= 6) return [3, 2];
    return [3, 3];
  };
  
  const [columns, rows] = getGridDimensions(count);
  const avatarSize = containerSize / Math.max(columns, rows);
  
  const getGridColumn = (index: number): string => {
    // For 3 items in a 2x2 grid
    if (columns === 2 && count === 3 && index === 2) {
      return '1 / 3'; // Span from column 1 to 3 (effectively centering)
    }
    // For odd items in 3-column layout
    if (columns === 3 && index === count - 1 && count % 2 === 1) {
      return '2';
    }
    return 'auto';
  };
  return (
    <Box
      sx={{
        position: "relative",
        width: containerSize,
        height: containerSize,
        borderRadius: "50%",
        overflow: "hidden",
        display: "grid",
        gap: 0,
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        backgroundColor: "#f0f0f0",
        border: "1px solid rgba(0, 0, 0, 0.87)",
        alignItems: "center",
        justifyItems: "center",
        alignContent: "center",
        justifyContent: "center",
      }}
    >
      {names.map((name, index) => (
        <Avatar
          key={index}
          src={name === "Diplicity" ? "/otto.png" : variant?.Flags[name]}
          sx={{
            width: `${avatarSize}px`,
            height: `${avatarSize}px`,
            fontSize: `${avatarSize / 2}px`,
            bgcolor: `hsl(${(index * 137.5) % 360}, 70%, 45%)`,
            gridColumn: getGridColumn(index),
          }}
        >
          {name[0]?.toUpperCase()}
        </Avatar>
      ))}
    </Box>
  );
};

export { ChannelAvatarGroup };
