import { Stack, Typography, Button, IconButton } from "@mui/material";
import { QueryContainer } from "..";
import { Close as CloseIcon } from "@mui/icons-material";
import { useCreateOrder } from "../../common/hooks/use-create-order";

const CreateOrder: React.FC = () => {
  const { query, handleClose, handleChange, isSubmitting } = useCreateOrder();

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) => {
        return (
          <Stack sx={styles.container}>
            <Stack sx={styles.titleCloseContainer}>
              <Typography>Create Order</Typography>
              <IconButton onClick={handleClose}>
                <CloseIcon />
              </IconButton>
            </Stack>
            <Stack sx={styles.optionGroupsContainer}>
              {data.map((optionGroup, index) => (
                <Stack key={index} sx={styles.labelOptionsContainer}>
                  <Typography variant="caption">{optionGroup.label}</Typography>
                  <Stack sx={styles.optionsContainer}>
                    {optionGroup.options.map((option) => (
                      <Button
                        key={option.key}
                        variant={option.selected ? "contained" : "outlined"}
                        onClick={() => handleChange(option.key, index)}
                        disabled={isSubmitting}
                      >
                        {option.label}
                      </Button>
                    ))}
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </Stack>
        );
      }}
    </QueryContainer>
  );
};

const styles: Styles = {
  container: {
    width: "100%",
  },
  titleCloseContainer: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexDirection: "row",
  },
  optionGroupsContainer: {
    width: "100%",
  },
  labelOptionsContainer: {
    width: "100%",
    gap: 1,
  },
  optionsContainer: {
    flexDirection: "row",
    gap: 1,
  },
};

export { CreateOrder };
