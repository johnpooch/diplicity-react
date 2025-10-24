import React from "react";
import {
  Button,
  FormControl,
  MenuItem,
  Stack,
  TextField,
  Skeleton,
  Alert,
  AlertTitle,
  InputLabel,
  Select,
} from "@mui/material";
import { service } from "../../store";
import { IconName } from "../../components/Icon";
import { useFormik } from "formik";
import { randomGameName } from "../../util";
import { Table } from "../../components/Table";
import { InteractiveMap } from "../../components/InteractiveMap/InteractiveMap";
import { useNavigate } from "react-router";

const initialValues = {
  sandboxGame: {
    name: randomGameName(),
    variantId: "classical",
  },
};

const CreateSandboxGame: React.FC = () => {
  const navigate = useNavigate();
  const query = service.endpoints.variantsList.useQuery(undefined);
  const [createSandboxGameMutationTrigger, createSandboxGameQuery] =
    service.endpoints.sandboxGameCreate.useMutation();

  const handleSubmit = async (values: {
    sandboxGame: { name: string; variantId: string };
  }) => {
    await createSandboxGameMutationTrigger(values).unwrap();
    navigate("/");
  };

  const formik = useFormik<{
    sandboxGame: { name: string; variantId: string };
  }>({
    initialValues,
    onSubmit: handleSubmit,
  });

  const selectedSandboxVariant = query.data?.find(
    v => v.id === formik.values.sandboxGame.variantId
  );

  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        formik.handleSubmit();
      }}
    >
      <Alert severity="info">
        <AlertTitle>Sandbox Mode</AlertTitle>
        Practice Diplomacy by controlling all nations yourself. Perfect for:
        <ul>
          <li>Learning game mechanics and order types</li>
          <li>Testing strategies and scenarios</li>
          <li>Exploring different variants</li>
        </ul>
        Sandbox games are private, have no time limits, and resolve when you're
        ready.
      </Alert>
      <Stack spacing={2} padding={2}>
        <TextField
          label="Game Name"
          variant="standard"
          name="name"
          value={formik.values.sandboxGame.name}
          onChange={e =>
            formik.setFieldValue("sandboxGame.name", e.target.value)
          }
          onBlur={formik.handleBlur}
          disabled={createSandboxGameQuery.isLoading}
          fullWidth
          required
        />

        <FormControl fullWidth>
          <InputLabel>Variant</InputLabel>
          {query.isLoading ? (
            <Skeleton variant="rectangular" width="100%" height={48} />
          ) : (
            <Select
              value={formik.values.sandboxGame.variantId}
              onChange={e =>
                formik.setFieldValue("sandboxGame.variantId", e.target.value)
              }
              disabled={createSandboxGameQuery.isLoading}
              required
            >
              {query.data?.map(variant => (
                <MenuItem key={variant.id} value={variant.id}>
                  {variant.name}
                </MenuItem>
              ))}
            </Select>
          )}
        </FormControl>

        {query.isLoading ? (
          <Skeleton variant="rectangular" width="100%" height={400} />
        ) : selectedSandboxVariant?.templatePhase ? (
          <InteractiveMap
            variant={selectedSandboxVariant}
            phase={selectedSandboxVariant.templatePhase}
            interactive={false}
            selected={[]}
            orders={undefined}
            style={{ width: "100%", height: "100%" }}
          />
        ) : null}

        <Table
          rows={[
            {
              label: "Number of nations",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedSandboxVariant?.nations.length.toString()
              ),
              icon: IconName.Players,
            },
            {
              label: "Start year",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedSandboxVariant?.templatePhase.year.toString()
              ),
              icon: IconName.StartYear,
            },
            {
              label: "Original author",
              value: query.isLoading ? (
                <Skeleton variant="text" width={100} />
              ) : (
                selectedSandboxVariant?.author
              ),
              icon: IconName.Author,
            },
          ]}
        />

        <Button
          variant="contained"
          color="primary"
          type="submit"
          disabled={
            createSandboxGameQuery.isLoading ||
            !formik.values.sandboxGame.name ||
            !formik.values.sandboxGame.variantId
          }
        >
          Create Sandbox Game
        </Button>
      </Stack>
    </form>
  );
};

export { CreateSandboxGame };
