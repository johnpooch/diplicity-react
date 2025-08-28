import React from "react";
import { Alert, Divider, Link } from "@mui/material";
import { Warning as WarningIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";
import { service } from "../store";

const NotificationBanner: React.FC = () => {
  const query = service.endpoints.devicesList.useQuery(undefined);
  const navigate = useNavigate();

  const handleLinkClick = (
    event: React.MouseEvent<HTMLAnchorElement, MouseEvent>
  ) => {
    event.preventDefault();
    navigate("/profile");
  };

  if (query.data && !query.data.find((device) => device.type === "web")) {
    return (
      <>
        <Alert severity="warning" icon={<WarningIcon />}>
          You have not enabled notifications. You will not receive
          messages or phase updates unless you enable notifications.{" "}
          <Link href="/profile" onClick={handleLinkClick}>
            Update notification settings
          </Link>
          .
        </Alert>
        <Divider />
      </>
    );
  }
};

export { NotificationBanner };
