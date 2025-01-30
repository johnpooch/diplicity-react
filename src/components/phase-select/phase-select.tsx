import {
  Stack,
  IconButton,
  FormControl,
  Select,
  MenuItem,
  styled,
  InputBase,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import {
  ArrowLeft as PreviousIcon,
  ArrowRight as NextIcon,
} from "@mui/icons-material";
import { usePhaseSelect } from "./use-phase-select";

const StyledInput = styled(InputBase)``;

const StyledSelect = styled(Select)``;

const StyledFormControl = styled(FormControl)`
  min-width: 250px;
`;

const StyledIconButton = styled(IconButton)`
  height: fit-content;
`;

const PhaseSelect = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const {
    handleNext,
    handlePhaseSelect,
    handlePrevious,
    selectedPhase,
    query,
    nextDisabled,
    previousDisabled,
  } = usePhaseSelect();

  if (!query.data) return null;

  return (
    <Stack direction="row" alignItems="center">
      {!isMobile && (
        <StyledIconButton
          edge="start"
          color="inherit"
          aria-label="back"
          onClick={handlePrevious}
          disabled={previousDisabled}
        >
          <PreviousIcon />
        </StyledIconButton>
      )}
      <StyledFormControl>
        <StyledSelect
          value={selectedPhase}
          onChange={(event) => handlePhaseSelect(event.target.value as number)}
          input={<StyledInput />}
        >
          {query.data.map(({ key, label }) => (
            <MenuItem key={key} value={key}>
              {label}
            </MenuItem>
          ))}
        </StyledSelect>
      </StyledFormControl>
      {!isMobile && (
        <StyledIconButton
          edge="end"
          color="inherit"
          aria-label="forward"
          onClick={handleNext}
          disabled={nextDisabled}
        >
          <NextIcon />
        </StyledIconButton>
      )}
    </Stack>
  );
};

export { PhaseSelect };
