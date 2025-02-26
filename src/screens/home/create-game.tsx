import React from "react";
import { useFormik } from "formik";
import {
  Stack,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
  FormControl,
  FormHelperText,
  Divider,
  Typography,
  ListItemText,
  ListItem,
  ListItemIcon,
} from "@mui/material";
import {
  People as PlayersIcon,
  Flag as WinConditionIcon,
  CalendarToday as StartYearIcon,
  Person as AuthorIcon,
} from "@mui/icons-material";
import { toFormikValidationSchema } from "zod-formik-adapter";
import service, { newGameSchema } from "../../common/store/service";
import { z } from "zod";
import { useNavigate } from "react-router";
import { QueryContainer, TableListItem } from "../../components";
import { randomGameName } from "../../util";

const initialValues = {
  Anonymous: false,
  ChatLanguageISO639_1: "",
  Desc: randomGameName(),
  DisableConferenceChat: false,
  DisableGroupChat: false,
  DisablePrivateChat: false,
  FirstMember: {
    NationPreferences: "",
  },
  GameMasterEnabled: false,
  LastYear: 0,
  MaxHated: null,
  MaxHater: 0,
  MaxRating: 0,
  MinQuickness: 0,
  MinRating: 0,
  MinReliability: 0,
  NationAllocation: 0,
  NonMovementPhaseLengthMinutes: 0,
  PhaseLengthMinutes: 1440,
  Private: false,
  RequireGameMasterInvitation: false,
  SkipMuster: true,
  Variant: "Classical",
  phaseLengthUnit: "day",
};

const styles: Styles = {
  listSubheader: (theme) => ({
    textAlign: "left",
    color: theme.palette.text.primary,
  }),
  listItemIcon: (theme) => ({
    color: theme.palette.text.primary,
    minWidth: "fit-content",
    padding: 1,
  }),
  listItemPrimaryText: (theme) => ({
    color: theme.palette.text.primary,
  }),
};

const useCreateGame = () => {
  const navigate = useNavigate();

  const query = service.endpoints.listVariants.useQuery(undefined);
  const [createGameMutationTrigger, createGameQuery] =
    service.endpoints.createGame.useMutation();

  const handleSubmit = async (values: z.infer<typeof newGameSchema>) => {
    await createGameMutationTrigger({
      ...values,
    }).unwrap();
    navigate("/");
  };

  return { query, handleSubmit, isSubmitting: createGameQuery.isLoading };
};

const getPhaseLengthDivider = (unit: string) =>
  unit === "day" ? 1440 : unit === "hour" ? 60 : 1;

const CreateGame: React.FC = () => {
  const { query, handleSubmit, isSubmitting } = useCreateGame();

  const formik = useFormik<
    z.infer<typeof newGameSchema> & {
      phaseLengthUnit: string;
    }
  >({
    initialValues,
    validationSchema: toFormikValidationSchema(newGameSchema),
    onSubmit: handleSubmit,
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        formik.handleSubmit(e);
      }}
    >
      <QueryContainer query={query}>
        {(data) => {
          const variant = data.find((v) => v.Name === formik.values.Variant);
          if (!variant) throw new Error("Variant not found");

          const phaseLengthDivider = getPhaseLengthDivider(
            formik.values.phaseLengthUnit
          );

          const phaseLengthValue = Math.floor(
            formik.values.PhaseLengthMinutes / phaseLengthDivider
          );

          return (
            <Stack spacing={2} padding={2}>
              <Typography variant="h4" sx={{ margin: 0 }}>
                General
              </Typography>
              <FormControl>
                <TextField
                  label="Game Name"
                  variant="standard"
                  name="name"
                  value={formik.values.Desc}
                  onChange={(e) => formik.setFieldValue("Desc", e.target.value)}
                  onBlur={formik.handleBlur}
                  error={formik.touched.Desc && Boolean(formik.errors.Desc)}
                  helperText={formik.touched.Desc && formik.errors.Desc}
                  disabled={isSubmitting}
                />
              </FormControl>
              <FormControl>
                <FormControlLabel
                  control={
                    <Checkbox
                      name="isPrivate"
                      checked={formik.values.Private}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      disabled={isSubmitting}
                    />
                  }
                  label="Private"
                />
                <FormHelperText>
                  Private games do not appear in the Find Games list. You must
                  send a link to the game to invite players.
                </FormHelperText>
              </FormControl>
              <FormControl>
                <Stack direction="row">
                  <TextField
                    label="Phase Length"
                    variant="standard"
                    name="phaseLength"
                    value={phaseLengthValue}
                    onChange={(e) =>
                      formik.setFieldValue(
                        "PhaseLengthMinutes",
                        parseInt(e.target.value) * phaseLengthDivider
                      )
                    }
                    onBlur={formik.handleBlur}
                    error={
                      formik.touched.PhaseLengthMinutes &&
                      Boolean(formik.errors.PhaseLengthMinutes)
                    }
                    helperText={
                      formik.touched.PhaseLengthMinutes &&
                      formik.errors.PhaseLengthMinutes
                    }
                    disabled={isSubmitting}
                  />
                  <TextField
                    select
                    label="Unit"
                    variant="standard"
                    name="phaseLengthUnit"
                    value={formik.values.phaseLengthUnit}
                    onChange={(e) => {
                      formik.setFieldValue("phaseLengthUnit", e.target.value);
                    }}
                    disabled={isSubmitting}
                  >
                    <MenuItem value="minute">Minutes</MenuItem>
                    <MenuItem value="hour">Hours</MenuItem>
                    <MenuItem value="day">Days</MenuItem>
                  </TextField>
                </Stack>
                <FormHelperText>
                  The length of each phase in the game.
                </FormHelperText>
              </FormControl>
              <Divider />
              <Typography variant="h4" sx={{ margin: 0 }}>
                Variant
              </Typography>
              <TextField
                select
                label="Variant"
                variant="standard"
                name="variant"
                value={formik.values.Variant}
                onChange={(e) =>
                  formik.setFieldValue("Variant", e.target.value)
                }
                onBlur={formik.handleBlur}
                error={formik.touched.Variant && Boolean(formik.errors.Variant)}
                helperText={formik.touched.Variant && formik.errors.Variant}
                disabled={isSubmitting}
              >
                {data.map((variant) => (
                  <MenuItem key={variant.Name} value={variant.Name}>
                    {variant.Name}
                  </MenuItem>
                ))}
              </TextField>

              <img
                style={{ maxWidth: "100%", maxHeight: "100%" }}
                src={`https://diplicity-engine.appspot.com/Variant/${variant.Name}/Map.svg`}
                alt={variant.Name}
              />
              <TableListItem
                label="Number of nations"
                value={variant.Nations.length.toString()}
                icon={<PlayersIcon />}
              />
              <TableListItem
                label="Start year"
                value={variant.Start.Year.toString()}
                icon={<StartYearIcon />}
              />
              <TableListItem
                label="Original author"
                value={variant.CreatedBy}
                icon={<AuthorIcon />}
              />
              <ListItem>
                <ListItemIcon sx={styles.listItemIcon}>
                  <WinConditionIcon />
                </ListItemIcon>
                <ListItemText
                  primary={"Win condition"}
                  secondary={variant.Rules}
                  sx={styles.listItemPrimaryText}
                />
              </ListItem>
              <Button
                variant="contained"
                color="primary"
                type="submit"
                disabled={isSubmitting}
              >
                Create
              </Button>
            </Stack>
          );
        }}
      </QueryContainer>
    </form>
  );
};

export { CreateGame };
