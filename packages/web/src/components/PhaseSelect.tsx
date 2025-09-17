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

  const previousDisabled = phase.ordinal === 1;
  const nextDisabled = phase.ordinal === game.phases.length;

  const handlePhaseSelect = (phase: number) => {
    setSelectedPhase(phase);
  };

  const handleNext = () => {
    setSelectedPhase(selectedPhase + 1);
  };

  const handlePrevious = () => {
    setSelectedPhase(selectedPhase - 1);
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
