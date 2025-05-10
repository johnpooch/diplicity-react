import React from "react";
import { useFormik } from "formik";
import {
  Stack,
  TextField,
  MenuItem,
  Button,
  FormControl,
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
import { service } from "../../store";
import { useNavigate } from "react-router";
import { QueryContainer, TableListItem } from "../../components";
import { randomGameName } from "../../util";

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

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        formik.handleSubmit(e);
      }}
    >
      <QueryContainer query={query}>
        {(variants) => {
          const selectedVariant = variants.find(
            (v) => v.id === formik.values.variant
          );
          if (!selectedVariant) throw new Error("Variant not found");
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
                  value={formik.values.name}
                  onChange={(e) => formik.setFieldValue("name", e.target.value)}
                  onBlur={formik.handleBlur}
                  disabled={createGameQuery.isLoading}
                />
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
                value={formik.values.variant}
                onChange={(e) =>
                  formik.setFieldValue("variant", e.target.value)
                }
                disabled={createGameQuery.isLoading}
              >
                {variants.map((variant) => (
                  <MenuItem key={variant.id} value={variant.id}>
                    {variant.name}
                  </MenuItem>
                ))}
              </TextField>

              <img
                style={{ maxWidth: "100%", maxHeight: "100%" }}
                src={`https://diplicity-engine.appspot.com/Variant/${selectedVariant.name}/Map.svg`}
                alt={selectedVariant.name}
              />
              <TableListItem
                label="Number of nations"
                value={selectedVariant.nations.length.toString()}
                icon={<PlayersIcon />}
              />
              <TableListItem
                label="Start year"
                value={"TODO"}
                icon={<StartYearIcon />}
              />
              <TableListItem
                label="Original author"
                value={selectedVariant.author}
                icon={<AuthorIcon />}
              />
              <ListItem>
                <ListItemIcon sx={styles.listItemIcon}>
                  <WinConditionIcon />
                </ListItemIcon>
                <ListItemText
                  primary={"Win condition"}
                  secondary={selectedVariant.description}
                  sx={styles.listItemPrimaryText}
                />
              </ListItem>
              <Button
                variant="contained"
                color="primary"
                type="submit"
                disabled={createGameQuery.isLoading}
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

export { CreateGame };
