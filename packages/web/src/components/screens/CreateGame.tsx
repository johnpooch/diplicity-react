import React from "react";
import {
  Button,
  Divider,
  FormControl,
  MenuItem,
  Stack,
  TextField,
  Typography,
  Skeleton,
} from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { service } from "../../store";
import { HomeAppBar } from "../composites/HomeAppBar";
import { IconName } from "../elements/Icon";
import { useNavigate } from "react-router";
import { useFormik } from "formik";
import { randomGameName } from "../../util";
import { Table } from "../elements/Table";

const initialValues = {
  name: randomGameName(),
  variant: "classical",
};

const CreateGame: React.FC = () => {
  const navigate = useNavigate();
  const query = service.endpoints.variantsList.useQuery(undefined);
  const [createGameMutationTrigger, createGameQuery] =
    service.endpoints.gameCreate.useMutation();

  const handleSubmit = async (
    values: Parameters<typeof createGameMutationTrigger>[0]["gameCreateRequest"]
  ) => {
    await createGameMutationTrigger({ gameCreateRequest: values }).unwrap();
    navigate("/");
  };

  const formik = useFormik<
    Parameters<typeof createGameMutationTrigger>[0]["gameCreateRequest"]
  >({
    initialValues,
    onSubmit: handleSubmit,
  });

  const selectedVariant = query.data?.find(v => v.id === formik.values.variant);

  return (
    <HomeLayout
      appBar={<HomeAppBar title="Create Game" />}
      content={
        <form
          onSubmit={e => {
            e.preventDefault();
            formik.handleSubmit(e);
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
            <Divider />
            <Typography variant="h4">Variant</Typography>
            {query.isLoading ? (
              <Skeleton variant="rectangular" width="100%" height={48} />
            ) : (
              <TextField
                select
                label="Variant"
                variant="standard"
                name="variant"
                value={formik.values.variant}
                onChange={e => formik.setFieldValue("variant", e.target.value)}
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
            ) : (
              <img
                style={{ maxWidth: "100%", maxHeight: "100%" }}
                src={`https://diplicity-engine.appspot.com/Variant/${selectedVariant?.name}/Map.svg`}
                alt={selectedVariant?.name}
              />
            )}
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
                    selectedVariant?.start.year.toString()
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
      }
    />
  );
};

export { CreateGame };
