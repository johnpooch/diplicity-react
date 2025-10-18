import React from "react";
import {
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
  Skeleton,
  FormHelperText,
} from "@mui/material";
import {
  NationAssignmentEnum,
  MovementPhaseDurationEnum,
  service,
} from "../../store";
import { IconName } from "../../components/Icon";
import { useFormik } from "formik";
import { randomGameName } from "../../util";
import { Table } from "../../components/Table";
import { InteractiveMap } from "../../components/InteractiveMap/InteractiveMap";
import { useNavigate } from "react-router";

const initialValues = {
  name: randomGameName(),
  variantId: "classical",
  nationAssignment: "random" as NationAssignmentEnum,
  movementPhaseDuration: "24 hours" as MovementPhaseDurationEnum,
  private: false,
};

const CreateStandardGame: React.FC = () => {
  const navigate = useNavigate();
  const query = service.endpoints.variantsList.useQuery(undefined);
  const [createGameMutationTrigger, createGameQuery] =
    service.endpoints.gameCreate.useMutation();

  const handleSubmit = async (
    values: Parameters<typeof createGameMutationTrigger>[0]["game"]
  ) => {
    await createGameMutationTrigger({ game: values }).unwrap();
    navigate("/");
  };

  const formik = useFormik<
    Parameters<typeof createGameMutationTrigger>[0]["game"]
  >({
    initialValues,
    onSubmit: handleSubmit,
  });

  const selectedVariant = query.data?.find(
    v => v.id === formik.values.variantId
  );

  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        formik.handleSubmit();
      }}
    >
      <Stack spacing={2} padding={2}>
        <Typography variant="h4">General</Typography>
        <FormControl>
          <TextField
            label="Game Name"
            variant="standard"
            name="name"
            value={formik.values.name}
            onChange={e => formik.setFieldValue("name", e.target.value)}
            onBlur={formik.handleBlur}
            disabled={createGameQuery.isLoading}
          />
        </FormControl>
        <FormControl>
          <FormControlLabel
            control={
              <Checkbox
                checked={formik.values.private}
                onChange={e =>
                  formik.setFieldValue("private", e.target.checked)
                }
                disabled={createGameQuery.isLoading}
                name="private"
              />
            }
            label="Private"
          />
          <FormHelperText sx={{ margin: 0 }}>
            Make this game private (only accessible via direct link, not shown
            in public listings).
          </FormHelperText>
        </FormControl>
        <Typography variant="h4">Deadlines</Typography>
        <FormControl>
          <TextField
            select
            label="Phase Deadline"
            variant="standard"
            name="movementPhaseDuration"
            value={formik.values.movementPhaseDuration}
            onChange={e =>
              formik.setFieldValue("movementPhaseDuration", e.target.value)
            }
            disabled={createGameQuery.isLoading}
          >
            <MenuItem value="24 hours">24 hours</MenuItem>
            <MenuItem value="48 hours">48 hours</MenuItem>
            <MenuItem value="1 week">1 week</MenuItem>
          </TextField>
          <FormHelperText sx={{ margin: 0 }}>
            After the deadline, the phase will be automatically resolved.
          </FormHelperText>
        </FormControl>
        <Typography variant="h4">Variant</Typography>
        {query.isLoading ? (
          <Skeleton variant="rectangular" width="100%" height={48} />
        ) : (
          <TextField
            select
            label="Variant"
            variant="standard"
            name="variantId"
            value={formik.values.variantId}
            onChange={e => formik.setFieldValue("variantId", e.target.value)}
            disabled={createGameQuery.isLoading}
          >
            {query.data?.map(variant => (
              <MenuItem key={variant.id} value={variant.id}>
                {variant.name}
              </MenuItem>
            ))}
          </TextField>
        )}
        {query.isLoading ? (
          <Skeleton variant="rectangular" width="100%" height={400} />
        ) : selectedVariant?.templatePhase ? (
          <InteractiveMap
            variant={selectedVariant}
            phase={selectedVariant.templatePhase}
            interactive={false}
            selected={[]}
            orders={undefined}
          />
        ) : null}
        <Table
          rows={[
            {
              label: "Number of nations",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedVariant?.nations.length.toString()
              ),
              icon: IconName.Players,
            },
            {
              label: "Start year",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedVariant?.templatePhase.year.toString()
              ),
              icon: IconName.StartYear,
            },
            {
              label: "Original author",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedVariant?.author
              ),
              icon: IconName.Author,
            },
          ]}
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

export { CreateStandardGame };
