import React from "react";
import { useFormik } from "formik";
import {
  Stack,
  Typography,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
} from "@mui/material";
import { toFormikValidationSchema } from "zod-formik-adapter";
import service, { newGameSchema } from "../common/store/service";
import { z } from "zod";
import { useDispatch } from "react-redux";
import { feedbackActions } from "../common/store/feedback";
import { useNavigate } from "react-router";

const CreateGame: React.FC = () => {
  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);

  const [createGameMutationTrigger, createGameQuery] =
    service.endpoints.createGame.useMutation();

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const formik = useFormik<z.infer<typeof newGameSchema>>({
    initialValues: {
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
    },
    validationSchema: toFormikValidationSchema(newGameSchema),
    onSubmit: async (values) => {
      try {
        await createGameMutationTrigger({
          ...values,
        }).unwrap();
        navigate("/");
        dispatch(
          feedbackActions.setFeedback({
            severity: "success",
            message: "Game created successfully",
          })
        );
      } catch {
        dispatch(
          feedbackActions.setFeedback({
            severity: "error",
            message: "Something went wrong",
          })
        );
      }
    },
  });

  if (listVariantsQuery.isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        formik.handleSubmit(e);
      }}
    >
      <Stack spacing={2}>
        <Typography variant="h1">Create Game</Typography>
        <TextField
          label="Game Name"
          variant="outlined"
          name="name"
          value={formik.values.Desc}
          onChange={(e) => formik.setFieldValue("Desc", e.target.value)}
          onBlur={formik.handleBlur}
          error={formik.touched.Desc && Boolean(formik.errors.Desc)}
          helperText={formik.touched.Desc && formik.errors.Desc}
          disabled={createGameQuery.isLoading}
        />
        <TextField
          select
          label="Variant"
          variant="outlined"
          name="variant"
          value={formik.values.Variant}
          onChange={(e) => formik.setFieldValue("Variant", e.target.value)}
          onBlur={formik.handleBlur}
          error={formik.touched.Variant && Boolean(formik.errors.Variant)}
          helperText={formik.touched.Variant && formik.errors.Variant}
          disabled={createGameQuery.isLoading}
        >
          {listVariantsQuery.data?.map((variant) => (
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
              disabled={createGameQuery.isLoading}
            />
          }
          label="Private"
        />
        <Button
          variant="contained"
          color="primary"
          type="submit"
          disabled={createGameQuery.isLoading}
        >
          Create
        </Button>
      </Stack>
    </form>
  );
};

export default CreateGame;
