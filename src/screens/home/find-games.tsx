import React from "react";
import {
  Stack,
  Typography,
  IconButton,
  Avatar,
  Button,
  Link,
  ListItem,
  ListItemAvatar,
  ListItemText,
  List,
} from "@mui/material";
import { MoreHoriz as MenuIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { ScreenTopBar } from "./screen-top-bar";
import { service } from "../../common";

const options = { my: false, mastered: false };

const useFindGames = () => {
  const { endpoints } = service;
  const query = endpoints.listGames.useQuery({
    ...options,
    status: "Open",
  });
  return { query };
};

const FindGames: React.FC = () => {
  const { query } = useFindGames();

  return (
    <>
      <ScreenTopBar title="Find Games" />
      <List sx={{ width: "100%" }} disablePadding>
        <QueryContainer query={query}>
          {(games) =>
            games.map((game) => (
              <ListItem
                alignItems="center"
                divider
                secondaryAction={
                  <IconButton edge="end" aria-label="delete">
                    <MenuIcon />
                  </IconButton>
                }
              >
                <ListItemAvatar>
                  <Avatar alt="Remy Sharp" src="/static/images/avatar/1.jpg" />
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Link href="#" underline="hover">
                      <Typography>{game.Desc}</Typography>
                    </Link>
                  }
                  secondary={
                    <Stack gap={1}>
                      <Stack direction="row" gap={1}>
                        <Typography variant="caption">
                          {game.Variant}
                        </Typography>
                        <Typography variant="caption">
                          {game.PhaseLengthMinutes}
                        </Typography>
                      </Stack>
                      <Button
                        sx={{
                          justifyContent: "flex-start",
                          width: "fit-content",
                        }}
                      >
                        <Stack direction="row" spacing={-1} alignItems="center">
                          {game.Members.map((member) => (
                            <Avatar
                              sx={{
                                width: 24,
                                height: 24,
                              }}
                              key={member.User.Id}
                              src={member.User.Picture}
                            />
                          ))}
                        </Stack>
                      </Button>
                    </Stack>
                  }
                />
              </ListItem>
            ))
          }
        </QueryContainer>
      </List>
    </>
  );
};

export { FindGames };
