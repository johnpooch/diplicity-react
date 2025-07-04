import { useMediaQuery, useTheme } from "@mui/material";

interface Responsiveness {
    device: "mobile" | "tablet" | "desktop";
}

const useResponsiveness = (): Responsiveness => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
    const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
    const isDesktop = useMediaQuery(theme.breakpoints.up("md"));

    if (isMobile) {
        return { device: "mobile" };
    } else if (isTablet) {
        return { device: "tablet" };
    } else if (isDesktop) {
        return { device: "desktop" };
    }

    throw new Error("No responsive device found");
}

export { useResponsiveness };