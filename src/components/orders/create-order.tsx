import { useState } from "react";
import { Stack, Typography, Button, IconButton } from "@mui/material";
import { QueryContainer } from "..";
import { useGameDetailContext } from "../../context";
import {
  mergeQueries,
  useCreateOrderMutation,
  useListHydratedOptionsQuery,
} from "../../common";
import { Close as CloseIcon } from "@mui/icons-material";
import { useCreateOrderContext } from "../../context/create-order-context";

/**
 * We transform the options tree into a flat array of options to simplify the
 * rendering logic.
 */
type GroupedOptions = {
  label: string;
  options: { key: string; label: string; selected?: boolean }[];
}[];

type Node = Record<string, { Name?: string; Next: Node; Type: string }>;

const createOptionFromNode = ([key, value]: [string, { Name?: string }]) => ({
  key,
  label: value.Name ? value.Name : key,
});

const useCreateOrder = () => {
  const { gameId } = useGameDetailContext();
  const { source, setSource } = useCreateOrderContext();
  if (!source) throw new Error("Source is not defined");
  const [createOrder, createOrderMutation] = useCreateOrderMutation(gameId);
  const listOptionsQuery = useListHydratedOptionsQuery(gameId);
  const [selectedOptions, setSelectedOptions] = useState([source]);

  const orderType = selectedOptions[1];

  const getLabel = (node: Node) => {
    const nodeType = Object.values(node)[0]?.Type;
    if (nodeType === "OrderType") {
      return "Select order type";
    }
    if (nodeType === "Province") {
      if (orderType === "Move" || orderType === "Retreat") {
        return "Select destination";
      }
      if (orderType === "Support" || orderType === "Convoy") {
        return selectedOptions.length === 2
          ? `Select province to ${orderType.toLowerCase()}`
          : "Select a destination";
      }
    }
    return "Select an option";
  };

  const query = mergeQueries([listOptionsQuery], (options) => {
    let currentNode = options[source].Next;

    const groupedOptions: GroupedOptions = [];

    selectedOptions.slice(1).forEach((step) => {
      // Convert the current node to an array of options and set selected option
      const options = Object.entries(currentNode)
        .map(createOptionFromNode)
        .map((option) => ({
          ...option,
          selected: step === option.key,
        }));
      // Push the transformed options to the array and define the label
      groupedOptions.push({
        label: getLabel(currentNode),
        options,
      });
      // Advance to the next node
      currentNode = currentNode[step].Next;
    });

    // If there is a next node, add it to the transformed array
    if (Object.keys(currentNode).length > 0) {
      const nextOptions = Object.entries(currentNode).map(createOptionFromNode);
      groupedOptions.push({
        label: getLabel(currentNode),
        options: nextOptions,
      });
    }

    return groupedOptions;
  });

  const handleClose = () => {
    setSource(undefined);
  };

  const handleCreateOrder = async (order: string[]) => {
    await createOrder(order);
    setSource(undefined);
  };

  const handleChange = (selectedOption: string, level: number) => {
    const options = listOptionsQuery.data;
    if (!options) throw new Error("Option is not defined");

    const newSelectedOptions = selectedOptions.slice(0, level + 1);
    newSelectedOptions.push(selectedOption);
    setSelectedOptions(newSelectedOptions);

    // Check if there is a next node
    let currentNode = options[source].Next;
    newSelectedOptions.slice(1).forEach((step) => {
      currentNode = currentNode[step].Next;
    });
    if (Object.keys(currentNode).length === 0) {
      handleCreateOrder(newSelectedOptions);
    }
  };

  const isSubmitting = createOrderMutation.isLoading;

  return {
    query,
    handleCreateOrder,
    handleClose,
    handleChange,
    isSubmitting,
  };
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

export { CreateOrder };
