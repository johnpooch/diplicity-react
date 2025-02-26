import { createTheme } from "@mui/material";

const theme = createTheme({
    typography: {
        fontFamily: "'Cabin', sans-serif",
        h1: {
            fontSize: "18px",
            lineHeight: "22px",
            fontWeight: 800,
            marginBottom: "8px",
        },
        h2: {
            fontSize: "16px",
            lineHeight: "20px",
            fontWeight: 600,
        },
        h4: {
            fontSize: "16px",
            lineHeight: "24px",
            fontWeight: 600,
        },
        caption: {
            fontSize: "12px",
            lineHeight: "18px",
            color: "rgb(89, 99, 110)"
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
    components: {
        MuiAppBar: {
            styleOverrides: {
                root: ({ theme }) => ({
                    backgroundColor: theme.palette.background.default,
                    color: theme.palette.text.primary,
                }),
            },
        },
        MuiTypography: {
            styleOverrides: {
                root: {
                    textAlign: "left",
                },
            },
        },
        MuiListItem: {
            styleOverrides: {
                root: {
                    border: "none",
                },
            },
        },
        MuiAlert: {
            styleOverrides: {
                root: {
                    textAlign: "left",
                },
            },
        },
        MuiListSubheader: {
            styleOverrides: {
                root: {
                    textAlign: "left",
                },
            },
        },
        MuiMenuItem: {
            styleOverrides: {
                root: ({ theme }) => ({
                    "& .MuiListItemIcon-root": {
                        color: theme.palette.text.primary,
                    },
                }),
            },
        }
    }
});

export default theme;