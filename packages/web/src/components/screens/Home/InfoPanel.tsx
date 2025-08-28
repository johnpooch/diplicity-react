import { Link, Stack, Typography } from "@mui/material";
import { createUseStyles } from "../../utils/styles";

const useStyles = createUseStyles(() => ({
    infoContainer: {
        width: 240,
        position: "sticky",
        padding: 2,
        top: 0,
        alignSelf: "flex-start",
        height: "100vh",
        overflow: "auto",
        gap: 1,
    },
    infoTitle: {
        fontWeight: 600,
    },
}));

const HomeInfoPanel: React.FC = (props) => {
    const styles = useStyles(props);

    const learnLink =
        "https://diplicity.notion.site/Diplicity-FAQ-7b4e0a119eb54c69b80b411f14d43bb9";
    const discordLink =
        "https://discord.com/channels/565625522407604254/697344626859704340";

    return (
        <Stack sx={styles.infoContainer}>
            <Typography variant="body1" sx={styles.infoTitle}>
                Welcome to Diplicity!
            </Typography>
            <Typography variant="body2" color="textSecondary">
                If you're new to the game, read our{" "}
                <Link href={learnLink} target="_blank" rel="noreferrer">
                    FAQ
                </Link>
                .
            </Typography>
            <Typography variant="body2" color="textSecondary">
                To chat with the developers or meet other players, join our{" "}
                <Link href={discordLink} target="_blank" rel="noreferrer">
                    Discord community
                </Link>
                .
            </Typography>
        </Stack>
    );
};

export { HomeInfoPanel }