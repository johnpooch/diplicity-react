import React from "react";
import { Alert, AlertTitle, Divider, Link } from "@mui/material";
import { Warning as WarningIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";
import { useMessaging } from "../context";

const NotificationBanner: React.FC = () => {
  const { enabled, isLoading } = useMessaging();
  const navigate = useNavigate();

  const handleLinkClick = (
    event: React.MouseEvent<HTMLAnchorElement, MouseEvent>
  ) => {
    event.preventDefault();
    navigate("/profile");
  };

  // Don't show banner while loading initial state
  if (isLoading) {
    return null;
  }

  if (!enabled) {
    return (
      <>
        <Alert severity="warning" icon={<WarningIcon />}>
          <AlertTitle>Notifications Disabled</AlertTitle>
          You have not enabled notifications. You will not receive messages or
          phase updates unless you enable notifications.{" "}
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
