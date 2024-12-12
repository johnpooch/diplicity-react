import React from "react";
import { Chip } from "@mui/material";
import { green, yellow, red } from "@mui/material/colors";

const StatusChip: React.FC<{
  status: "confirmed" | "pending" | "unconfirmed" | "missed";
  label: string;
}> = ({ status, label }) => {
  let bgColor;
  const textColor = "black";

  switch (status) {
    case "confirmed":
      bgColor = green[500];
      break;
    case "pending":
    case "unconfirmed":
      bgColor = yellow[500];
      break;
    case "missed":
      bgColor = red[500];
      break;
    default:
      bgColor = "default";
  }

  return (
    <Chip
      label={label}
      style={{
        backgroundColor: bgColor,
        color: textColor,
        fontWeight: 600,
        height: 24,
      }}
    />
  );
};

export default StatusChip;
