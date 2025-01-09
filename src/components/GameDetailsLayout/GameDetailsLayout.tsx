import { Outlet } from "react-router";
import {
  AppBar,
  FormControl,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Toolbar,
  useTheme,
  InputBase,
  styled,
} from "@mui/material";
import {
  ArrowBack as BackIcon,
  ExpandMore as ExpandMoreIcon,
  ArrowLeft as PreviousIcon,
  ArrowRight as NextIcon,
} from "@mui/icons-material";

const StyledInput = styled(InputBase)`
  color: ${({ theme }) => theme.palette.secondary.main};
`;

const GameDetailsLayout: React.FC<{
  onClickBack: () => void;
  onClickCreateOrder: () => void;
  actions: React.ReactNode[];
  navigation: React.ReactNode;
  modals: React.ReactNode[];
}> = (props) => {
  const theme = useTheme();

  const CustomExpandMoreIcon = () => (
    <ExpandMoreIcon
      {...props}
      style={{ color: theme.palette.secondary.main }}
    />
  );

  return (
    <Stack
      sx={{
        width: "100vw",
        height: "calc(100vh - 56px)",
        background: theme.palette.background.default,
      }}
    >
      <AppBar position="static">
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={props.onClickBack}
          >
            <BackIcon />
          </IconButton>
          <Stack direction="row" alignItems="center">
            <IconButton
              sx={{ height: "fit-content" }}
              edge="start"
              color="inherit"
              aria-label="back"
            >
              <PreviousIcon />
            </IconButton>
            <FormControl sx={{ m: 1, minWidth: 120 }}>
              <Select
                labelId="demo-simple-select-standard-label"
                id="demo-simple-select-standard"
                value={1}
                onChange={() => {}}
                label="Phase"
                IconComponent={CustomExpandMoreIcon}
                input={<StyledInput />}
              >
                <MenuItem value={1}>Spring 1900, Movement</MenuItem>
                <MenuItem value={2}>Spring 1900, Retreat</MenuItem>
              </Select>
            </FormControl>
            <IconButton
              sx={{ height: "fit-content" }}
              edge="end"
              color="inherit"
              aria-label="forward"
            >
              <NextIcon />
            </IconButton>
          </Stack>
          <Stack></Stack>
        </Toolbar>
      </AppBar>
      <Outlet />
      <Stack
        direction="row"
        spacing={2}
        alignItems="center"
        sx={{
          position: "fixed",
          bottom: 16 + 50,
          right: 16,
        }}
      >
        {props.actions}
      </Stack>
      {props.navigation}
      {props.modals}
    </Stack>
  );
};

export { GameDetailsLayout };
