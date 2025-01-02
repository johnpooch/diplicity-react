import React from "react";
import { CircularProgress, Box } from "@mui/material";
import { useMap } from "./use-map";

const MapContainer: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      flexGrow="1"
    >
      {children}
    </Box>
  );
};

const Map: React.FC = () => {
  const { isLoading, isError, isSuccess, data } = useMap();

  if (isLoading) {
    return (
      <MapContainer>
        <CircularProgress />
      </MapContainer>
    );
  }

  if (isError) return <div>Error loading map</div>;
  if (!isSuccess) return null;

  return (
    <MapContainer>
      <div
        dangerouslySetInnerHTML={{ __html: data }}
        style={{ maxWidth: "100%", height: "100%" }}
      />
    </MapContainer>
  );
};

export { Map };
