import React from "react";
import {
  Stack,
  IconButton,
  FormControl,
  Select,
  MenuItem,
  InputBase,
} from "@mui/material";
import {
  ArrowLeft as PreviousIcon,
  ArrowRight as NextIcon,
} from "@mui/icons-material";
import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { createUseStyles } from "./utils/styles";
import { useResponsiveness } from "./utils/responsive";

const useStyles = createUseStyles(() => ({
  root: {
    alignItems: "center",
    borderRadius: 5,
    paddingLeft: 1,
    paddingRight: 1,
    border: theme => `1px solid ${theme.palette.divider}`,
    flexGrow: 1,
  },
  formControl: {
  },
  iconButton: {
    height: "fit-content",
  },
}));

const PhaseSelect: React.FC = () => {
  const styles = useStyles({});
  const responsiveness = useResponsiveness();
  const isMobile = responsiveness.device === "mobile";

  const { gameRetrieveQuery } = useSelectedGameContext();
  const { selectedPhase, setSelectedPhase } = useSelectedPhaseContext();

  if (gameRetrieveQuery.isLoading) {
    return null;
  }

  if (gameRetrieveQuery.isError || !gameRetrieveQuery.data) {
    return null;
  }

  const game = gameRetrieveQuery.data;
  const phase = game.phases.find(p => p.id === selectedPhase);
  if (!phase) throw new Error("Phase not found");

  // Sort phases by ordinal to ensure proper ordering
  const sortedPhases = [...game.phases].sort((a, b) => a.ordinal - b.ordinal);
  const currentPhaseIndex = sortedPhases.findIndex(p => p.id === selectedPhase);

  const previousDisabled = currentPhaseIndex === 0;
  const nextDisabled = currentPhaseIndex === sortedPhases.length - 1;

  const handlePhaseSelect = (phaseId: number) => {
    setSelectedPhase(phaseId);
  };

  const handleNext = () => {
    if (currentPhaseIndex < sortedPhases.length - 1) {
      const nextPhase = sortedPhases[currentPhaseIndex + 1];
      setSelectedPhase(nextPhase.id);
    }
  };

  const handlePrevious = () => {
    if (currentPhaseIndex > 0) {
      const previousPhase = sortedPhases[currentPhaseIndex - 1];
      setSelectedPhase(previousPhase.id);
    }
  };

  return (
    <Stack direction="row" alignItems="center" sx={styles.root}>
      {!isMobile && (
        <Stack>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={handlePrevious}
            disabled={previousDisabled}
            sx={styles.iconButton}
          >
            <PreviousIcon />
          </IconButton>
        </Stack>
      )}
      <Stack flexGrow={1}>
        <FormControl sx={styles.formControl}>
          <Select
            value={selectedPhase}
            onChange={event => handlePhaseSelect(event.target.value as number)}
            input={<InputBase />}
          >
            {game.phases.map(phase => (
              <MenuItem key={phase.id} value={phase.id}>
                {phase.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>
      {!isMobile && (
        <Stack>
          <IconButton
            edge="end"
            color="inherit"
            aria-label="forward"
            onClick={handleNext}
            disabled={nextDisabled}
            sx={styles.iconButton}
          >
            <NextIcon />
          </IconButton>
        </Stack>
      )}
    </Stack>
  );
};

export { PhaseSelect };
