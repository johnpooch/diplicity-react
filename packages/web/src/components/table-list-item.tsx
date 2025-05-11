import { ListItem, ListItemIcon, ListItemText } from "@mui/material";

const TableListItem: React.FC<{
  label: string;
  value: string | undefined;
  icon: React.ReactElement;
}> = ({ label, value, icon }) => {
  return (
    <ListItem>
      <ListItemIcon sx={styles.listItemIcon}>{icon}</ListItemIcon>
      <ListItemText primary={label} sx={styles.listItemPrimaryText} />
      <ListItemText primary={value} sx={styles.listItemSecondaryText} />
    </ListItem>
  );
};

const styles: Styles = {
  listItemIcon: (theme) => ({
    color: theme.palette.text.primary,
    minWidth: "fit-content",
    padding: 1,
  }),
  listItemPrimaryText: (theme) => ({
    color: theme.palette.text.primary,
  }),
  listItemSecondaryText: (theme) => ({
    color: theme.palette.text.secondary,
    paddingRight: 1,
    "& .MuiListItemText-primary": {
      textAlign: "right",
    },
  }),
};

export { TableListItem };
