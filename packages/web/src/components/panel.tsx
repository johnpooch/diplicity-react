import { Box, Divider, Stack } from "@mui/material";

const styles: Styles = {
  root: {
    flexGrow: 1,
    overflow: "hidden",
  },
  content: {
    flexGrow: 1,
    overflowY: "auto",
  },
  footer: {
    height: "auto",
    padding: 1,
    alignItems: "flex-end",
  },
};

type PanelProps = {
  children: React.ReactNode;
};

type ContentProps = {
  children: React.ReactNode;
};

type FooterProps = {
  children: React.ReactNode;
  divider?: boolean;
};

const Panel: React.FC<PanelProps> & {
  Content: React.FC<ContentProps>;
  Footer: React.FC<FooterProps>;
} = (props) => {
  return <Stack sx={styles.root}>{props.children}</Stack>;
};

const Content: React.FC<ContentProps> = (props) => {
  return <Box sx={styles.content}>{props.children}</Box>;
};

const Footer: React.FC<FooterProps> = (props) => {
  return (
    <>
      {props.divider && <Divider />}
      <Stack sx={styles.footer}>{props.children}</Stack>
    </>
  );
};

Panel.Content = Content;
Panel.Footer = Footer;

export { Panel };
