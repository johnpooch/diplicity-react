import React from "react";
import { QueryContainer } from "./query-container";
import { useGetUserConfigQuery } from "../common";
import { Alert, Divider, Link } from "@mui/material";
import { Warning as WarningIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";

const NotificationBanner: React.FC = () => {
  const query = useGetUserConfigQuery();
  const navigate = useNavigate();

  const handleLinkClick = (
    event: React.MouseEvent<HTMLAnchorElement, MouseEvent>
  ) => {
    event.preventDefault();
    navigate("/profile");
  };

  return (
    <QueryContainer query={query} onRenderLoading={() => null}>
      {(data) =>
        data.MailConfig?.Enabled ||
        (data.FCMToken && !data.FCMToken.Disabled) ? null : (
          <>
            <Alert severity="warning" icon={<WarningIcon />}>
              You have not enabled any notifications. You will not receive
              messages or phase updates unless you enable at least one
              notification type.{" "}
              <Link href="/profile" onClick={handleLinkClick}>
                Update notification settings
              </Link>
              .
            </Alert>
            <Divider />
          </>
        )
      }
    </QueryContainer>
  );
};

export { NotificationBanner };
