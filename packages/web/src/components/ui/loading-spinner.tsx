import { Loader2, type LucideProps } from "lucide-react";
import { cn } from "@/lib/utils";

const spinnerSizeClasses = {
  sm: "size-4",
  md: "size-6",
  lg: "size-10",
} as const;

export type LoadingSpinnerSize = keyof typeof spinnerSizeClasses;

export type LoadingSpinnerProps = Omit<
  LucideProps,
  "children" | "size"
> & {
  label?: string | null;
  size?: LoadingSpinnerSize;
};

const spinnerClassName = (
  size: LoadingSpinnerSize,
  className?: string
): string =>
  cn("loading-spinner animate-spin", spinnerSizeClasses[size], className);

const accessibilityProps = (label: string | null) =>
  label === null
    ? ({ "aria-hidden": true } as const)
    : ({ "aria-label": label, role: "status" } as const);

function LoadingSpinner({
  className,
  label = "Loading",
  size = "md",
  ...props
}: LoadingSpinnerProps) {
  return (
    <Loader2
      data-slot="loading-spinner"
      className={spinnerClassName(size, className)}
      {...accessibilityProps(label)}
      {...props}
    />
  );
}

export function createLoadingSpinnerElement({
  className,
  label = null,
  size = "md",
}: Pick<LoadingSpinnerProps, "className" | "label" | "size"> = {}): HTMLElement {
  const host = document.createElement("span");
  const spinner = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  spinner.dataset.slot = "loading-spinner";
  spinner.setAttribute(
    "class",
    cn("lucide lucide-loader-circle", spinnerClassName(size, className))
  );
  spinner.setAttribute("viewBox", "0 0 24 24");
  spinner.setAttribute("fill", "none");
  spinner.setAttribute("stroke", "currentColor");
  spinner.setAttribute("stroke-width", "2");
  spinner.setAttribute("stroke-linecap", "round");
  spinner.setAttribute("stroke-linejoin", "round");
  if (label === null) {
    spinner.setAttribute("aria-hidden", "true");
  } else {
    spinner.setAttribute("aria-label", label);
    spinner.setAttribute("role", "status");
  }
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M21 12a9 9 0 1 1-6.219-8.56");
  spinner.appendChild(path);
  host.appendChild(spinner);
  return host;
}

export { LoadingSpinner };
