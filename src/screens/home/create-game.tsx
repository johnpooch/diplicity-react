import React from "react";
import { useFormik } from "formik";
import {
  Stack,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
} from "@mui/material";
import { toFormikValidationSchema } from "zod-formik-adapter";
import service, { newGameSchema } from "../../common/store/service";
import { z } from "zod";
import { useNavigate } from "react-router";
import { QueryContainer } from "../../components";
import { ScreenTopBar } from "./screen-top-bar";

const initialValues = {
  Anonymous: false,
  ChatLanguageISO639_1: "",
  Desc: "",
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

const CreateGame: React.FC = () => {
  const { query, handleSubmit, isSubmitting } = useCreateGame();

  const formik = useFormik<z.infer<typeof newGameSchema>>({
    initialValues,
    validationSchema: toFormikValidationSchema(newGameSchema),
    onSubmit: handleSubmit,
  });

  return (
    <>
      <ScreenTopBar title="Create Game" />
      <form
        onSubmit={(e) => {
          e.preventDefault();
          formik.handleSubmit(e);
        }}
      >
        <QueryContainer query={query}>
          {(data) => (
            <Stack spacing={2} padding={2}>
              <TextField
                label="Game Name"
                variant="outlined"
                name="name"
                value={formik.values.Desc}
                onChange={(e) => formik.setFieldValue("Desc", e.target.value)}
                onBlur={formik.handleBlur}
                error={formik.touched.Desc && Boolean(formik.errors.Desc)}
                helperText={formik.touched.Desc && formik.errors.Desc}
                disabled={isSubmitting}
              />
              <TextField
                select
                label="Variant"
                variant="outlined"
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
              <Button
                variant="contained"
                color="primary"
                type="submit"
                disabled={isSubmitting}
              >
                Create
              </Button>
            </Stack>
          )}
        </QueryContainer>
      </form>
    </>
  );
};

export { CreateGame };
