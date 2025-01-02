import { createTheme } from "@mui/material";

const theme = createTheme({
    typography: {
        h1: {
            fontSize: "28px",
            lineHeight: "34px",
            fontWeight: 600,
            marginBottom: "8px",
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
    palette: {
        primary: {
            main: "#281A1A",
            contrastText: "#FDE2B5",
        },
        secondary: {
            main: "#FDE2B5",
        },
    },
});

export default theme;