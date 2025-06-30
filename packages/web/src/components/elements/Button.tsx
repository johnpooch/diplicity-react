import React from "react";
import {
    ListItemButton as MuiListItemButton,
    ListItemIcon,
    ListItemText,
    Stack,
    IconButton as MuiIconButton,
    IconButtonProps as MuiIconButtonProps,
} from "@mui/material";

import { Icon, IconName } from "./Icon";
import { createUseStyles } from "../utils/styles";

interface ListItemButtonProps {
    onClick: () => void;
    selected: boolean;
    icon: IconName;
    label?: string;
    "aria-label": string;
}

const useListItemButtonStyles = createUseStyles<ListItemButtonProps>(
    (props, theme) => ({
        text: {
            color: props.selected ? theme.palette.primary.main : undefined,
            fontWeight: props.selected ? "bold" : "normal",
            fontSize: 18,
        },
        icon: {
            color: props.selected ? theme.palette.primary.main : undefined,
            fontWeight: props.selected ? "bold" : "normal",
        },
        iconContainer: {
            minWidth: "fit-content",
            alignItems: "center",
        },
    })
);

const ListItemButton: React.FC<ListItemButtonProps> = (props) => {
    const styles = useListItemButtonStyles(props);

    return (
        <MuiListItemButton onClick={props.onClick} aria-label={props["aria-label"]}>
            <Stack direction="row" gap={1}>
                <ListItemIcon sx={styles.iconContainer}>
                    <Icon name={props.icon} sx={styles.icon} />
                </ListItemIcon>
                {props.label && (
                    <ListItemText
                        primary={props.label}
                        primaryTypographyProps={{
                            sx: styles.text,
                        }}
                    />
                )}
            </Stack>
        </MuiListItemButton>
    );
};

interface IconButtonProps extends MuiIconButtonProps {
    icon: IconName;
}
const IconButton: React.FC<IconButtonProps> = ({ icon, ...rest }) => {
    return (
        <MuiIconButton {...rest}>
            <Icon name={icon} />
        </MuiIconButton>
    );
};

export { ListItemButton, IconButton };
