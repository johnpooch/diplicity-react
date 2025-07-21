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
import { QueryContainer } from "./query-container";
import { useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { useParams } from "react-router";

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

  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("Game ID is required");

  const { selectedPhase, setSelectedPhase } = useSelectedPhaseContext();

  const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
    gameId,
  });

  return (
    <QueryContainer query={gameRetrieveQuery} onRenderLoading={() => <></>}>
      {game => {
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
                onChange={event =>
                  handlePhaseSelect(event.target.value as number)
                }
                input={<StyledInput />}
              >
                {game.phases.map(phase => (
                  <MenuItem key={phase.id} value={phase.id}>
                    {phase.name}
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
      }}
    </QueryContainer>
  );
};

export { PhaseSelect };
