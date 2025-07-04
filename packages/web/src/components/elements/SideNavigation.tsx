import { Drawer, List } from "@mui/material";
import { IconName } from "./Icon";
import { createUseStyles } from "../utils/styles";
import { IconButton, ListItemButton } from "./Button";

interface SideNavigationProps {
    options: {
        label: string;
        icon: IconName;
        value: string;
    }[];
    selectedValue: string;
    onChange: (value: string) => void;
    variant: "expanded" | "collapsed";
}

const useStyles = createUseStyles<SideNavigationProps>((props) => ({
    root: {
        width: props.variant === "expanded" ? 240 : 56,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
            position: props.variant === "expanded" ? "relative" : "fixed",
            width: props.variant === "expanded" ? 240 : 56,
            boxSizing: "border-box",
            border: "none",
        },
    },
}))

const SideNavigation: React.FC<SideNavigationProps> = (props) => {
    const styles = useStyles(props);

    return (
        <Drawer
            variant="permanent"
            sx={styles.root}
        >
            <List>
                {props.options.map((option) => props.variant === "expanded" ? (
                    <ListItemButton
                        key={option.value}
                        selected={option.value === props.selectedValue}
                        onClick={() => props.onChange(option.value)}
                        icon={option.icon}
                        label={option.label}
                        aria-label={option.label}
                    />
                ) : (
                    <IconButton
                        key={option.value}
                        icon={option.icon}
                        onClick={() => props.onChange(option.value)}
                        aria-label={option.label}
                    />
                ))}
            </List>
        </Drawer>
    )
}

export { SideNavigation };
