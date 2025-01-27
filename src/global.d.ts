import { SxProps, Theme } from "@mui/material";

declare global {
    type Styles = Record<string, SxProps<Theme>>;
}