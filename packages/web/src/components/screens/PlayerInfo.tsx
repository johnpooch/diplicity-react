import React from "react";
import {
  Alert,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Skeleton,
  Stack,
} from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { service } from "../../store";
import { HomeAppBar } from "../composites/HomeAppBar";
import { useNavigate, useParams } from "react-router";

const PlayerInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
  const navigate = useNavigate();

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <HomeAppBar title="Player Info" onNavigateBack={() => navigate(-1)} />
      }
      bottomNavigation={<div></div>}
      content={
        <Stack>
          <>
            {query.data && query.data.status === "pending" && (
              <Alert severity="info">
                This game has not started yet. The game will start once{" "}
                {query.data.variant.nations.length} players have joined.
              </Alert>
            )}
            <List>
              {query.data
                ? query.data.members.map(member => (
                    <ListItem key={member.username}>
                      <ListItemAvatar>
                        <Avatar src={member.picture} alt={member.username} />
                      </ListItemAvatar>
                      <ListItemText primary={member.username} />
                    </ListItem>
                  ))
                : Array.from({ length: 3 }, (_, index) => (
                    <ListItem key={index}>
                      <ListItemAvatar>
                        <Skeleton variant="circular" width={40} height={40} />
                      </ListItemAvatar>
                      <ListItemText
                        primary={<Skeleton variant="text" width={150} />}
                      />
                    </ListItem>
                  ))}
            </List>
          </>
        </Stack>
      }
    />
  );
};

export { PlayerInfo };
