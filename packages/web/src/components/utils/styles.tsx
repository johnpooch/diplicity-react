import { useMemo } from "react";
import { useTheme } from "@mui/material";
import { SxProps, Theme } from "@mui/material";

type StyleFunction<TProps> = (props: TProps, theme: Theme) => Record<string, SxProps<Theme>>;

function createUseStyles<TProps>(
    styleFunction: StyleFunction<TProps>
) {
    return function useStyles(props: TProps): Record<string, SxProps<Theme>> {
        const theme = useTheme();

        return useMemo(() => {
            return styleFunction(props, theme);
        }, [styleFunction, props, theme]);
    };
}

export { createUseStyles };