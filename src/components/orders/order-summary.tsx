import { Chip, Stack, Typography } from "@mui/material";

/**
 * Renders an order as text, with a chip indicating the type of order.
 */
const OrderSummary: React.FC<OrderSummaryProps> = (props) => {
  const { source, unitType, destination, aux, type } = props;

  const getOrderSummary = () => {
    switch (type) {
      case "Hold":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="hold" />
          </OrderSummaryContainer>
        );
      case "Disband":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="disband" />
          </OrderSummaryContainer>
        );
      case "Build":
        return (
          <OrderSummaryContainer>
            <OrderSummaryChip label="Build" />
            <OrderSummaryText>
              {unitType} in {source}
            </OrderSummaryText>
          </OrderSummaryContainer>
        );
      case "Move":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="move to" />
            <OrderSummaryText>{destination}</OrderSummaryText>
          </OrderSummaryContainer>
        );
      case "Retreat":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="retreat to" />
            <OrderSummaryText>{destination}</OrderSummaryText>
          </OrderSummaryContainer>
        );
      case "MoveViaConvoy":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="move via convoy to" />
            <OrderSummaryText>{destination}</OrderSummaryText>
          </OrderSummaryContainer>
        );
      case "Support":
        return aux === destination ? (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="support" />
            <OrderSummaryText>{aux} to</OrderSummaryText>
            <OrderSummaryChip label="hold" />
          </OrderSummaryContainer>
        ) : (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="support" />
            <OrderSummaryText>
              {aux} to {destination}
            </OrderSummaryText>
          </OrderSummaryContainer>
        );
      case "Convoy":
        return (
          <OrderSummaryContainer>
            <OrderSummaryText>
              {unitType} {source}
            </OrderSummaryText>
            <OrderSummaryChip label="convoy" />
            <OrderSummaryText>
              {aux} to {destination}
            </OrderSummaryText>
          </OrderSummaryContainer>
        );
      default:
        return null;
    }
  };

  return <>{getOrderSummary()}</>;
};

const OrderSummaryChip: React.FC<{ label: string }> = ({ label }) => (
  <Chip sx={styles.chip} size="small" label={label} />
);

const OrderSummaryText: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => <Typography>{children}</Typography>;

const OrderSummaryContainer: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <Stack direction="row" alignItems="center" gap={1}>
    {children}
  </Stack>
);

type OrderSummaryProps = {
  source: string;
  unitType?: string;
  destination?: string;
  aux?: string;
  type?: string;
};

const styles: Styles = {
  chip: (theme) => ({
    backgroundColor: theme.palette.secondary.main,
    color: theme.palette.secondary.contrastText,
    fontWeight: 800,
    borderRadius: theme.shape.borderRadius,
    "& .MuiChip-label": {
      padding: theme.spacing(0.5, 1),
    },
  }),
};

export { OrderSummary };
