import { StepIconProps, useTheme } from "@mui/material";

const CreateOrderStepIcon: React.FC<StepIconProps> = (props) => {
  const theme = useTheme();

  const backgroundColor = props.active
    ? theme.palette.primary.main
    : theme.palette.secondary.main;

  return (
    <div
      style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: backgroundColor,
      }}
    />
  );
};

export { CreateOrderStepIcon };
