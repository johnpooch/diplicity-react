import React from "react";
import {
    ListItem,
    ListItemAvatar,
    ListItemText,
    Skeleton,
    Stack,
} from "@mui/material";
import { createUseStyles } from "../utils/styles";

const useStyles = createUseStyles(() => ({
    listItem: (theme) => ({
        gap: 1,
        borderBottom: `1px solid ${theme.palette.divider}`,
        alignItems: "center",
    }),
    mapContainer: {
        display: "flex",
        width: 80,
    },
    contentStack: {
        flex: 1,
    },
    secondaryContainer: {
        gap: 1,
    },
    rulesContainer: {
        gap: 1,
        flexDirection: "row",
    },
    avatarStackContainer: {
        padding: "8px 0px"
    },
}));

const GameCardSkeleton: React.FC = (props) => {
    const styles = useStyles(props);

    return (
        <ListItem
            sx={styles.listItem}
            secondaryAction={
                <Skeleton variant="circular" width={24} height={24} />
            }
        >
            <ListItemAvatar sx={styles.mapContainer}>
                <Skeleton variant="rectangular" width={80} height={70} />
            </ListItemAvatar>
            <Stack sx={styles.contentStack}>
                <ListItemText
                    primary={
                        <Skeleton variant="text" width={200} height={24} />
                    }
                />
                <Stack sx={styles.secondaryContainer}>
                    <Stack sx={styles.rulesContainer}>
                        <Skeleton variant="text" width={80} height={16} />
                        <Skeleton variant="text" width={60} height={16} />
                    </Stack>
                    <Stack sx={styles.avatarStackContainer}>
                        <Skeleton variant="text" width={80} height={28} />
                    </Stack>
                </Stack>
            </Stack>
        </ListItem>
    );
};

export { GameCardSkeleton };
