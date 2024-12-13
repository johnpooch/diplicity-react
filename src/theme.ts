import { createTheme } from "@mui/material";

const theme = createTheme({
    typography: {
        h1: {
            fontSize: "32px",
            lineHeight: "36px",
            fontWeight: 600,
        },
        h2: {
            fontSize: "22px",
            lineHeight: "26px",
            fontWeight: 600,
        },
        button: {
            textTransform: "none",
        }
    },
});

export default theme;