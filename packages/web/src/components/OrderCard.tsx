import React from "react";
import { Stack, Typography } from "@mui/material";
import { OrderRead, ProvinceRead, Unit } from "../store";
import { createUseStyles } from "./utils/styles";
import { Icon, IconName } from "./Icon";

type OrderCardProps = {
  province: ProvinceRead;
  unit?: Unit;
  order?: OrderRead;
  primaryAction?: React.ReactNode;
};

const useStyles = createUseStyles<OrderCardProps>(() => ({
  mainContainer: theme => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
  }),
  nation: () => ({
    lineHeight: "1.8",
  }),
  successIcon: {
    fontSize: 14,
    color: theme => theme.palette.success.main,
  },
  failureIcon: {
    fontSize: 14,
    color: theme => theme.palette.error.main,
  },
  failureText: {
    color: theme => theme.palette.error.main,
  },
}));

const OrderCard: React.FC<OrderCardProps> = props => {
  const styles = useStyles(props);
  return (
    <Stack
      p={1}
      gap={1}
      direction="row"
      sx={styles.mainContainer}
      justifyContent="space-between"
    >
      <Stack direction="row" gap={2}>
        <Stack>
          <Stack direction="row" alignItems="flex-start" flexDirection="column">
            <Typography variant="body2" sx={styles.nation}>
              {props.unit?.type} {props.province.name}
            </Typography>
            {props.order ? (
              <Stack direction="column">
                <Stack direction="row" gap={1} alignItems="center">
                  <Typography variant="caption">
                    {props.order.summary}
                  </Typography>
                  {props.order.resolution?.status && (
                    <>
                      {props.order.resolution?.status === "Succeeded" && (
                        <Icon name={IconName.Success} sx={styles.successIcon} />
                      )}
                      {props.order.resolution?.status !== "Succeeded" && (
                        <>
                          <Icon
                            name={IconName.Failure}
                            sx={styles.failureIcon}
                          />
                          <Typography variant="caption" sx={styles.failureText}>
                            {props.order.resolution?.status}
                          </Typography>
                        </>
                      )}
                    </>
                  )}
                </Stack>
              </Stack>
            ) : (
              <Typography variant="caption">Order not provided</Typography>
            )}
          </Stack>
        </Stack>
      </Stack>
      {props.primaryAction}
    </Stack>
  );
};

export { OrderCard };
