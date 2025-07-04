import React from "react";
import {
  TableRow,
  TableContainer,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  Stack,
  ListItemText,
} from "@mui/material";
import { createUseStyles } from "../utils/styles";
import { Icon, IconName } from "./Icon";

interface TableRow {
  label: string;
  value: string | React.ReactNode | undefined;
  icon?: IconName;
}

interface TableProps {
  rows: TableRow[];
}

const useStyles = createUseStyles<TableProps>(() => ({
  tableContainer: {
    boxShadow: "none",
    backgroundColor: "transparent",
    width: "100%",
  },
  table: {},
  iconCell: theme => ({
    color: theme.palette.text.primary,
    padding: theme.spacing(1),
    width: "auto",
    borderBottom: "none",
  }),
  labelCell: theme => ({
    color: theme.palette.text.primary,
    borderBottom: "none",
    padding: theme.spacing(1, 2),
  }),
  valueCell: theme => ({
    color: theme.palette.text.secondary,
    textAlign: "right",
    borderBottom: "none",
    padding: theme.spacing(1, 2),
  }),
}));

const Table: React.FC<TableProps> = props => {
  const styles = useStyles(props);

  return (
    <TableContainer component={Paper} sx={styles.tableContainer}>
      <List>
        {props.rows.map((row, index) => (
          <ListItem key={index} sx={{ justifyContent: "space-between" }}>
            <Stack direction="row" alignItems="center">
              {row.icon && (
                <ListItemIcon sx={styles.iconCell}>
                  <Icon name={row.icon} />
                </ListItemIcon>
              )}
              <ListItemText primary={row.label} sx={styles.labelCell} />
            </Stack>
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="flex-end"
            >
              <ListItemText primary={row.value} sx={styles.valueCell} />
            </Stack>
          </ListItem>
        ))}
      </List>
    </TableContainer>
  );
};

export { Table };
