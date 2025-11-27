import { Box, Container, Typography } from "@mui/material";

export function MaintenanceMode() {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          textAlign: "center",
          gap: 3,
        }}
      >
        <Typography variant="h1">Maintenance Mode</Typography>
        <Typography variant="body1" color="text.secondary">
          We're currently performing scheduled maintenance to improve the
          experience. Please check back in a few minutes.
        </Typography>
      </Box>
    </Container>
  );
}
