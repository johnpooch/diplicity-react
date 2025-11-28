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
import { service } from "../store";

const useStyles = createUseStyles(() => ({
  root: {
    alignItems: "center",
    borderRadius: 5,
    paddingLeft: 1,
    paddingRight: 1,
    border: theme => `1px solid ${theme.palette.divider}`,
    flexGrow: 1,
  },
  formControl: {},
  iconButton: {
    height: "fit-content",
  },
}));

const PhaseSelect: React.FC = () => {
  const styles = useStyles({});
  const responsiveness = useResponsiveness();
  const isMobile = responsiveness.device === "mobile";

  const { gameId } = useSelectedGameContext();
  const { selectedPhase, setPhase, setPreviousPhase, setNextPhase } =
    useSelectedPhaseContext();

  const phasesQuery = service.endpoints.gamePhasesList.useQuery(
    { gameId: gameId ?? "" },
    { skip: !gameId }
  );

  if (phasesQuery.isLoading) {
    return null;
  }

  if (phasesQuery.isError || !phasesQuery.data) {
    return null;
  }

  const phases = phasesQuery.data;
  const phase = phases.find(p => p.id === selectedPhase);
  if (!phase) throw new Error("Phase not found");

  // Sort phases by ordinal to ensure proper ordering
  const sortedPhases = [...phases].sort((a, b) => a.ordinal - b.ordinal);
  const currentPhaseIndex = sortedPhases.findIndex(p => p.id === selectedPhase);

  const previousDisabled = currentPhaseIndex === 0;
  const nextDisabled = currentPhaseIndex === sortedPhases.length - 1;

  const handlePhaseSelect = (phaseId: number) => {
    setPhase(phaseId);
  };

  return (
    <Stack direction="row" alignItems="center" sx={styles.root}>
      {!isMobile && (
        <Stack>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={setPreviousPhase}
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
            {phases.map(phase => (
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
            onClick={setNextPhase}
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
