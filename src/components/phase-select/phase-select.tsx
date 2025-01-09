import {
  Stack,
  IconButton,
  FormControl,
  Select,
  MenuItem,
  styled,
  InputBase,
} from "@mui/material";
import {
  ArrowLeft as PreviousIcon,
  ArrowRight as NextIcon,
} from "@mui/icons-material";
import { usePhaseSelect } from "./use-phase-select";

const StyledInput = styled(InputBase)`
  color: ${({ theme }) => theme.palette.secondary.main};
`;

const StyledSelect = styled(Select)`
  color: ${({ theme }) => theme.palette.secondary.main};

  & .MuiSelect-icon {
    color: ${({ theme }) => theme.palette.secondary.main};
  }
`;

const StyledFormControl = styled(FormControl)`
  min-width: 250px;
`;

const PhaseSelect = () => {
  const {
    handleNext,
    handlePhaseSelect,
    handlePrevious,
    selectedPhase,
    phases,
    nextDisabled,
    previousDisabled,
  } = usePhaseSelect();
  return (
    <Stack direction="row" alignItems="center">
      <IconButton
        sx={{ height: "fit-content" }}
        edge="start"
        color="inherit"
        aria-label="back"
        onClick={handlePrevious}
        disabled={previousDisabled}
      >
        <PreviousIcon />
      </IconButton>
      <StyledFormControl>
        <StyledSelect
          value={selectedPhase}
          onChange={(event) => handlePhaseSelect(event.target.value as number)}
          input={<StyledInput />}
        >
          {phases.map(({ key, label }) => (
            <MenuItem key={key} value={key}>
              {label}
            </MenuItem>
          ))}
        </StyledSelect>
      </StyledFormControl>
      <IconButton
        sx={{ height: "fit-content" }}
        edge="end"
        color="inherit"
        aria-label="forward"
        onClick={handleNext}
        disabled={nextDisabled}
      >
        <NextIcon />
      </IconButton>
    </Stack>
  );
};

export { PhaseSelect };
