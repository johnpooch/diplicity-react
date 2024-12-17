import React from "react";
import {
  deepPurple,
  deepOrange,
  blue,
  green,
  red,
  pink,
} from "@mui/material/colors";
import { Avatar } from "@mui/material";

const SIZE = 28;
const FONT_SIZE = 14;

const getRandomColor = (username: string) => {
  const colors = [
    deepPurple[500],
    deepOrange[500],
    blue[500],
    green[500],
    red[500],
    pink[500],
  ];
  const hash = Array.from(username).reduce(
    (acc, char) => acc + char.charCodeAt(0),
    0
  );
  return colors[hash % colors.length];
};

const getContrastColor = (bgColor: string) => {
  const color = bgColor.substring(1); // remove #
  const rgb = parseInt(color, 16); // convert rrggbb to decimal
  const r = (rgb >> 16) & 0xff; // extract red
  const g = (rgb >> 8) & 0xff; // extract green
  const b = (rgb >> 0) & 0xff; // extract blue
  const luma = 0.299 * r + 0.587 * g + 0.114 * b; // per ITU-R BT.709
  return luma > 186 ? "black" : "white";
};

const PlayerAvatar: React.FC<{
  username: string;
  onClick?: () => void;
}> = ({ username, onClick }) => {
  const bgColor = getRandomColor(username);
  const textColor = getContrastColor(bgColor);

  return (
    <Avatar
      sx={{
        width: SIZE,
        height: SIZE,
        fontSize: FONT_SIZE,
        backgroundColor: bgColor,
        color: textColor,
      }}
      onClick={onClick}
    >
      {username[0].toUpperCase()}
    </Avatar>
  );
};

export default PlayerAvatar;
