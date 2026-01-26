import React from "react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

type PanelProps = {
  children: React.ReactNode;
  className?: string;
};

type ContentProps = {
  children: React.ReactNode;
  className?: string;
};

type FooterProps = {
  children: React.ReactNode;
  divider?: boolean;
  className?: string;
};

const Panel: React.FC<PanelProps> & {
  Content: React.FC<ContentProps>;
  Footer: React.FC<FooterProps>;
} = ({ children, className }) => {
  return (
    <div className={cn("flex flex-col flex-1 h-full overflow-hidden", className)}>
      {children}
    </div>
  );
};

const Content: React.FC<ContentProps> = ({ children, className }) => {
  return (
    <div className={cn("flex-1 min-h-0 overflow-y-auto", className)}>
      {children}
    </div>
  );
};

const Footer: React.FC<FooterProps> = ({ children, divider = false, className }) => {
  return (
    <>
      {divider && <Separator />}
      <div className={cn("flex items-end p-2", className)}>{children}</div>
    </>
  );
};

Panel.Content = Content;
Panel.Footer = Footer;

export { Panel };
