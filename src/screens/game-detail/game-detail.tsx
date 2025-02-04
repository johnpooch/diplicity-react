import {
  AppBar,
  Box,
  Card,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Modal,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";

import {
  ArrowBack as BackIcon,
  Add as CreateChannelIcon,
  MoreHoriz as MenuIcon,
  Info as InfoIcon,
  Person as PlayerInfoIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import { useLocation, useNavigate } from "react-router";
import { useState } from "react";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import { OrderList, QueryContainer } from "../../components";
import {
  useGetVariantQuery,
  useGetPhaseQuery,
  useGetMapSvgQuery,
  useGetUnitSvgQuery,
  mergeQueries,
  useOrders,
} from "../../common";
import { createMap } from "../../common/map/map";
import { PhaseSelect } from "../../components/phase-select";
import { ChannelList } from "./channel-list";
import { Channel } from "./channel";
import { CreateChannel } from "./create-channel";
import { GameInfo, PlayerInfo } from "../home";

const useMap = () => {
  const { gameId } = useGameDetailContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const getVariantQuery = useGetVariantQuery(gameId);
  const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
  const getMapSvgQuery = useGetMapSvgQuery(gameId);
  const getArmySvgQuery = useGetUnitSvgQuery(gameId, "Army");
  const getFleetSvgQuery = useGetUnitSvgQuery(gameId, "Fleet");

  const query = mergeQueries(
    [
      getVariantQuery,
      getPhaseQuery,
      getMapSvgQuery,
      getArmySvgQuery,
      getFleetSvgQuery,
    ],
    (variant, phase, mapSvg, armySvg, fleetSvg) => {
      return createMap(mapSvg, armySvg, fleetSvg, variant, phase);
    }
  );
  return { query };
};

const EmptyChannel: React.FC = () => {
  return (
    <Stack
      sx={{
        height: "100%",
        width: "100%",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Typography>Select a conversation</Typography>
    </Stack>
  );
};

const GameDetail: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { gameId } = useGameDetailContext();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const { query: mapQuery } = useMap();
  const { query: ordersQuery } = useOrders();

  const handleBack = () => {
    navigate("/");
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGameInfo = () => {
    navigate(`/game/${gameId}/game-info`);
    handleMenuClose();
  };

  const handleClickPlayerInfo = () => {
    navigate(`/game/${gameId}/player-info`);
    handleMenuClose();
  };

  const handleClickShare = () => {
    navigator.clipboard.writeText(`${window.location.origin}/game/${gameId}`);
    handleMenuClose();
  };

  const handleChangeTab = (_: unknown, newValue: number) => {
    switch (newValue) {
      case 0:
        navigate(`/game/${gameId}`);
        break;
      case 1:
        navigate(`/game/${gameId}/chat`);
        break;
    }
  };

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/create-channel`);
  };

  const selectedTab = location.pathname.includes("chat") ? 1 : 0;
  const selectedChannel =
    location.pathname.includes("channel") && location.pathname.split("/").pop();
  const isCreateChannel = location.pathname.includes("create-channel");

  const isGameInfo = location.pathname.includes("game-info");
  const isPlayerInfo = location.pathname.includes("player-info");

  return (
    <Stack>
      <AppBar position="relative">
        <Stack
          sx={(theme) => ({
            borderBottom: `1px solid ${theme.palette.divider}`,
          })}
          direction="row"
          justifyContent="center"
        >
          <Stack
            direction="row"
            justifyContent="space-between"
            sx={{
              width: "100%",
              maxWidth: "1000px",
            }}
          >
            <IconButton onClick={handleBack}>
              <BackIcon />
            </IconButton>
            <Tabs value={selectedTab} onChange={handleChangeTab}>
              <Tab label="Map" />
              <Tab label="Chat" />
            </Tabs>
            <IconButton edge="start" color="inherit" onClick={handleMenuOpen}>
              <MenuIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleClickGameInfo}>
                <InfoIcon sx={{ marginRight: 1 }} />
                Game info
              </MenuItem>
              <MenuItem onClick={handleClickPlayerInfo}>
                <PlayerInfoIcon sx={{ marginRight: 1 }} />
                Player info
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleClickShare}>
                <ShareIcon sx={{ marginRight: 1 }} />
                Share
              </MenuItem>
            </Menu>
          </Stack>
        </Stack>
      </AppBar>
      <Stack alignItems="center">
        {selectedTab === 0 ? (
          <Card
            sx={{
              maxWidth: 1000,
              width: "100%",
              marginTop: 4,
              // padding: 1,
              minHeight: "580px",
            }}
            elevation={3}
          >
            <Stack direction="row">
              <Stack
                sx={() => ({
                  flex: 2,
                  p: 1,
                })}
              >
                <QueryContainer query={mapQuery} onRenderLoading={() => <></>}>
                  {(map) => <div dangerouslySetInnerHTML={{ __html: map }} />}
                </QueryContainer>
              </Stack>
              <Stack sx={{ flex: 1, p: 1 }}>
                <Stack alignItems="center">
                  <PhaseSelect />
                </Stack>
                <Divider />
                <Stack sx={{ p: 2 }}>
                  <Typography variant="h2">Orders</Typography>
                  <QueryContainer
                    query={ordersQuery}
                    onRenderLoading={() => <></>}
                  >
                    {(data) => <OrderList orders={data} />}
                  </QueryContainer>
                </Stack>
              </Stack>
            </Stack>
          </Card>
        ) : (
          <Card
            sx={{
              maxWidth: 1000,
              width: "100%",
              marginTop: 4,
              // padding: 1,
              minHeight: "580px",
            }}
            elevation={3}
          >
            <Stack
              direction="row"
              sx={() => ({
                height: "580px",
              })}
            >
              <Stack
                sx={(theme) => ({
                  flex: 1,
                  borderRight: `1px solid ${theme.palette.divider}`,
                  height: "100%",
                })}
              >
                <Stack
                  sx={{
                    paddingLeft: 2,
                    paddingRight: 2,
                    paddingTop: 1,
                    paddingBottom: 1,
                  }}
                  direction="row"
                  justifyContent="space-between"
                >
                  <Stack direction="row" alignItems="center" gap={1}>
                    <Typography variant="h1" sx={{ marginBottom: 0 }}>
                      Conversations
                    </Typography>
                  </Stack>
                  <IconButton
                    edge="start"
                    color="inherit"
                    onClick={handleCreateChannel}
                  >
                    <CreateChannelIcon />
                  </IconButton>
                </Stack>
                <Divider />
                <ChannelList />
              </Stack>
              <Stack sx={{ flex: 2 }}>
                {isCreateChannel ? (
                  <CreateChannel />
                ) : selectedChannel ? (
                  <Channel />
                ) : (
                  <EmptyChannel />
                )}
              </Stack>
            </Stack>
          </Card>
        )}
      </Stack>
      {/* Render a modal if game info */}
      <Modal open={isGameInfo}>
        <Box
          sx={{
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            maxWidth: 600,
            width: "90%",
            height: "90%",
            backgroundColor: "white",
            boxShadow: "0 0 10px rgba(0,0,0,0.1)",
            overflow: "auto",
          }}
        >
          <GameInfo />
        </Box>
      </Modal>
      {/* Render a modal if player info */}
      <Modal open={isPlayerInfo}>
        <Box
          sx={{
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            maxWidth: 600,
            width: "90%",
            height: "90%",
            backgroundColor: "white",
            boxShadow: "0 0 10px rgba(0,0,0,0.1)",
            overflow: "auto",
          }}
        >
          <PlayerInfo />
        </Box>
      </Modal>
    </Stack>
  );
};

export { GameDetail };
