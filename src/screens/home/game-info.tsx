import React from "react";
import {
  Alert,
  Avatar,
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Menu,
  MenuItem,
  Stack,
} from "@mui/material";
import {
  Map as VariantIcon,
  TimerOutlined as DeadlinesIcon,
  Language as LanguageIcon,
  People as PlayersIcon,
  Flag as WinConditionIcon,
  CalendarToday as StartYearIcon,
  Person as AuthorIcon,
  Info as InfoIcon,
  MoreHoriz as MenuIcon,
  Add as JoinGameIcon,
  Remove as LeaveGameIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import { QueryContainer } from "../../components";
import {
  actions,
  mergeQueries,
  service,
  useGetVariantQuery,
  useJoinGameMutation,
  useLeaveGameMutation,
} from "../../common";
import { ScreenTopBar } from "./screen-top-bar";
import { useNavigate, useParams } from "react-router";
import { useDispatch } from "react-redux";

const styles: Styles = {
  listSubheader: (theme) => ({
    textAlign: "left",
    color: theme.palette.text.primary,
  }),
  listItemIcon: (theme) => ({
    color: theme.palette.text.primary,
    minWidth: "fit-content",
    padding: 1,
  }),
  listItemPrimaryText: (theme) => ({
    color: theme.palette.text.primary,
  }),
  listItemSecondaryText: (theme) => ({
    color: theme.palette.text.secondary,
    paddingRight: 1,
    "& .MuiListItemText-primary": {
      textAlign: "right",
    },
  }),
  avatarStackButton: {
    justifyContent: "flex-start",
    width: "fit-content",
  },
  avatarStackContainer: {
    alignItems: "center",
  },
  avatar: {
    width: 24,
    height: 24,
  },
};

const useGameInfo = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID not found");

  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);
  const dispatch = useDispatch();
  const [joinGame, joinGameMutation] = useJoinGameMutation(gameId);
  const [leaveGame, leaveGameMutation] = useLeaveGameMutation(gameId);

  const isSubmitting =
    joinGameMutation.isLoading || leaveGameMutation.isLoading;

  const handleShare = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}/game-info/${gameId}`
    );
    dispatch(actions.setFeedback({ message: "Link copied to clipboard" }));
  };

  const query = mergeQueries(
    [getGameQuery, getVariantQuery],
    (game, variant) => {
      return {
        game,
        variant,
      };
    }
  );

  return { query, joinGame, leaveGame, isSubmitting, handleShare };
};

const GameInfo: React.FC = () => {
  const navigate = useNavigate();
  const { query, joinGame, leaveGame, isSubmitting, handleShare } =
    useGameInfo();

  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleJoinGame = async () => {
    await joinGame();
  };

  const handleLeaveGame = async () => {
    await leaveGame();
  };

  const handleView = (gameId: string) => {
    navigate(`/game/${gameId}`);
  };

  const TableListItem: React.FC<{
    label: string;
    value: string | undefined;
    icon: React.ReactElement;
  }> = ({ label, value, icon }) => {
    return (
      <ListItem>
        <ListItemIcon sx={styles.listItemIcon}>{icon}</ListItemIcon>
        <ListItemText primary={label} sx={styles.listItemPrimaryText} />
        <ListItemText primary={value} sx={styles.listItemSecondaryText} />
      </ListItem>
    );
  };

  return (
    <>
      <ScreenTopBar
        title="Game info"
        menu={
          query.data?.game && (
            <>
              <IconButton edge="end" aria-label="menu" onClick={handleMenuOpen}>
                <MenuIcon />
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                {query.data?.game.Started && (
                  <MenuItem
                    onClick={() => {
                      handleView(query.data?.game.ID as string);
                      handleMenuClose();
                    }}
                    disabled={isSubmitting}
                  >
                    <VariantIcon sx={{ marginRight: 1 }} />
                    View game
                  </MenuItem>
                )}
                {query.data.game.canJoin && (
                  <MenuItem
                    onClick={async () => {
                      await handleJoinGame();
                      handleMenuClose();
                    }}
                    disabled={isSubmitting}
                  >
                    <JoinGameIcon sx={{ marginRight: 1 }} />
                    Join game
                  </MenuItem>
                )}
                {query.data.game.canLeave && (
                  <MenuItem
                    onClick={async () => {
                      await handleLeaveGame();
                      handleMenuClose();
                    }}
                    disabled={isSubmitting}
                  >
                    <LeaveGameIcon sx={{ marginRight: 1 }} />
                    Leave game
                  </MenuItem>
                )}
                <Divider />
                <MenuItem
                  onClick={() => {
                    handleShare();
                    handleMenuClose();
                  }}
                  disabled={isSubmitting}
                >
                  <ShareIcon sx={{ marginRight: 1 }} />
                  Share
                </MenuItem>
              </Menu>
            </>
          )
        }
      />
      <QueryContainer query={query}>
        {(data) => (
          <>
            {!data.game.Started && (
              <Alert severity="info" icon={<InfoIcon />}>
                This game has not started yet. The game will start once{" "}
                {data.variant.Nations.length} players have joined.
              </Alert>
            )}
            <List>
              <ListSubheader sx={styles.listSubheader}>
                Game settings
              </ListSubheader>
              <TableListItem
                label="Variant"
                value={data.variant.Name}
                icon={<VariantIcon />}
              />
              <TableListItem
                label="Phase deadlines"
                value={data.game.PhaseLengthMinutes}
                icon={<DeadlinesIcon />}
              />
              {data.game.NonMovementPhaseLengthMinutes && (
                <TableListItem
                  label="Non-movement phase deadlines"
                  value={data.game.PhaseLengthMinutes}
                  icon={<></>}
                />
              )}
              <Divider />
              <ListSubheader sx={styles.listSubheader}>
                Player settings
              </ListSubheader>
              {data.game.ChatLanguageISO639_1 && (
                <TableListItem
                  label="Language"
                  value={data.game.ChatLanguageISO639_1}
                  icon={<LanguageIcon />}
                />
              )}
              <ListItem
                secondaryAction={
                  <Button sx={styles.avatarStackButton}>
                    <Stack
                      sx={styles.avatarStackContainer}
                      direction="row"
                      spacing={-1}
                    >
                      {data.game.Members.map((member) => (
                        <Avatar
                          sx={styles.avatar}
                          key={member.User.Id}
                          src={member.User.Picture}
                        />
                      ))}
                    </Stack>
                  </Button>
                }
              >
                <ListItemIcon sx={styles.listItemIcon}>
                  <PlayersIcon />
                </ListItemIcon>
                <ListItemText
                  primary={"Players"}
                  sx={styles.listItemPrimaryText}
                />
              </ListItem>
              <Divider />
              <ListSubheader sx={styles.listSubheader}>
                Variant details
              </ListSubheader>
              <ListItem>
                <img
                  src={`https://diplicity-engine.appspot.com/Variant/${data.variant.Name}/Map.svg`}
                  alt={data.variant.Name}
                  style={{ width: "100%" }}
                />
              </ListItem>
              <TableListItem
                label="Number of nations"
                value={data.variant.Nations.length.toString()}
                icon={<PlayersIcon />}
              />
              <TableListItem
                label="Start year"
                value={data.variant.Start.Year.toString()}
                icon={<StartYearIcon />}
              />
              <TableListItem
                label="Original author"
                value={data.variant.CreatedBy}
                icon={<AuthorIcon />}
              />
              <ListItem>
                <ListItemIcon sx={styles.listItemIcon}>
                  <WinConditionIcon />
                </ListItemIcon>
                <ListItemText
                  primary={"Win condition"}
                  secondary={data.variant.Rules}
                  sx={styles.listItemPrimaryText}
                />
              </ListItem>
              <Divider />
            </List>
          </>
        )}
      </QueryContainer>
    </>
  );
};

export { GameInfo };
