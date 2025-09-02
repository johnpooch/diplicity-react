import { Avatar, Stack, Typography } from "@mui/material";
import { createUseStyles } from "./utils/styles";

const EMPTY_AVATAR_WIDTH = 40;
const TWENTY_PERCENT_OPACITY_HEX_SUFFIX = "33";
const BORDER_RADIUS = "16px";
const USER_BORDER_RADIUS = `${BORDER_RADIUS} ${BORDER_RADIUS} ${BORDER_RADIUS} 0`;
const NON_USER_BORDER_RADIUS = `${BORDER_RADIUS} ${BORDER_RADIUS} 0 ${BORDER_RADIUS}`;
const FALLBACK_BORDER_COLOR = "#a9a9a9";

type ChannelMessageProps = {
  name: string;
  message: string;
  date: string;
  showAvatar: boolean;
  avatar: string;
  color: string;
  isUser: boolean;
};

const useStyles = createUseStyles<ChannelMessageProps>((props) => ({
  container: {
    flexDirection: props.isUser ? "row" : "row-reverse",
    gap: 2,
  },
  messageAndDate: {
    minWidth: `50%`,
    alignItems: props.isUser ? "flex-start" : "flex-end",
  },
  message: {
    width: "100%",
    background: `${props.color}${TWENTY_PERCENT_OPACITY_HEX_SUFFIX}`,
    padding: 1,
    gap: 1,
    border: !colorIsVeryLight(props.color)
      ? `1px solid ${props.color}`
      : `1px solid ${FALLBACK_BORDER_COLOR}`,
    borderRadius: props.isUser ? USER_BORDER_RADIUS : NON_USER_BORDER_RADIUS,
  },
  emptyAvatar: {
    minWidth: EMPTY_AVATAR_WIDTH,
  },
}));

const ChannelMessage: React.FC<ChannelMessageProps> = (props) => {
  const styles = useStyles(props);
  return (
    <Stack sx={styles.container}>
      {props.showAvatar ? (
        <Avatar src={props.avatar} />
      ) : (
        <Stack sx={styles.emptyAvatar} />
      )}
      <Stack sx={styles.messageAndDate}>
        <Stack sx={styles.message}>
          <Typography variant="body2">{props.name}</Typography>
          <Typography>{props.message}</Typography>
        </Stack>
        <Typography variant="caption">{props.date}</Typography>
      </Stack>
      <Stack sx={styles.emptyAvatar} />
    </Stack>
  );
};

const colorIsVeryLight = (color: string): boolean => {
  const hex = color.replace("#", "");
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  return r + g + b > 500;
};

export { ChannelMessage };
