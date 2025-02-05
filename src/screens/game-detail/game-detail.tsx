import {
  AppBar,
  Box,
  Card,
  Divider,
  Fab,
  IconButton,
  Modal as MuiModal,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";

import {
  ArrowBack as BackIcon,
  Add as CreateChannelIcon,
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBoxOutlined as OrdersConfirmedIcon,
} from "@mui/icons-material";
import { useLocation, useNavigate } from "react-router";
import { useState } from "react";
import { useGameDetailContext } from "../../context";
import { OrderList, QueryContainer } from "../../components";
import { useOrders, useMap } from "../../common";
import { PhaseSelect } from "../../components/phase-select";
import { ChannelList } from "./channel-list";
import { Channel } from "./channel";
import { CreateChannel } from "./create-channel";
import { GameInfo, PlayerInfo } from "../home";
import { CreateOrder } from "./create-order";
import { GameDetailMenu } from "./game-detail-menu";

const styles: Styles = {
  appBar: {
    alignItems: "center",
    position: "relative",
  },
  appBarInner: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    maxWidth: 1000,
  },
  cardContainer: {
    alignItems: "center",
  },
  card: {
    maxWidth: 1000,
    width: "100%",
    marginTop: 4,
    minHeight: "580px",
  },
  cardInner: {
    height: "580px",
    flexDirection: "row",
  },
  mapContainer: {
    flex: 2,
  },
  ordersContainer: {
    flex: 1,
  },
  phaseSelectContainer: {
    alignItems: "center",
  },
  ordersAndButtonContainer: {
    flexGrow: 1,
    justifyContent: "space-between",
  },
  actionsContainer: {
    display: "flex",
    padding: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    justifyContent: "flex-end",
  },
  channelListContainer: (theme) => ({
    flex: 1,
    borderRight: `1px solid ${theme.palette.divider}`,
    height: "100%",
  }),
  channelContainer: {
    flex: 2,
  },
  header: {
    padding: "8px 16px",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  modalBox: (theme) => ({
    position: "fixed",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    maxWidth: 600,
    width: "90%",
    height: "90%",
    backgroundColor: "white",
    boxShadow: `0 0 10px ${theme.palette.divider}`,
    overflow: "auto",
  }),
  emptyChannel: {
    height: "100%",
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
  },
};

const EmptyChannel: React.FC = () => {
  return (
    <Stack sx={styles.emptyChannel}>
      <Typography>Select a conversation</Typography>
    </Stack>
  );
};

const Modal: React.FC<{ open: boolean; children: React.ReactElement }> = (
  props
) => {
  return (
    <MuiModal open={props.open} style={{ display: "block" }}>
      <Box sx={styles.modalBox}>{props.children}</Box>
    </MuiModal>
  );
};

const GameDetail: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { gameId } = useGameDetailContext();

  const [createOrderOpen, setCreateOrderOpen] = useState(false);

  const { query: mapQuery } = useMap();
  const {
    query: ordersQuery,
    handleToggleConfirmOrders,
    isSubmitting,
  } = useOrders();

  const handleBack = () => {
    navigate("/");
  };

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/create-channel`);
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

  const selectedTab = location.pathname.includes("chat") ? 1 : 0;
  const selectedChannel =
    location.pathname.includes("channel") && location.pathname.split("/").pop();

  const createChannelOpen = location.pathname.includes("create-channel");
  const gameInfoOpen = location.pathname.includes("game-info");
  const playerInfoOpen = location.pathname.includes("player-info");

  return (
    <Stack>
      <AppBar sx={styles.appBar}>
        <Stack sx={styles.appBarInner}>
          <IconButton onClick={handleBack}>
            <BackIcon />
          </IconButton>
          <Tabs value={selectedTab} onChange={handleChangeTab}>
            <Tab label="Map" />
            <Tab label="Chat" />
          </Tabs>
          <GameDetailMenu />
        </Stack>
      </AppBar>
      <Stack sx={styles.cardContainer}>
        {selectedTab === 0 ? (
          <Card sx={styles.card} elevation={3}>
            <Stack sx={styles.cardInner}>
              <Stack sx={styles.mapContainer}>
                <QueryContainer query={mapQuery} onRenderLoading={() => <></>}>
                  {(map) => <div dangerouslySetInnerHTML={{ __html: map }} />}
                </QueryContainer>
              </Stack>
              <Stack sx={styles.ordersContainer}>
                <Stack sx={styles.header}>
                  <Typography variant="h2">Orders</Typography>
                  <IconButton
                    edge="end"
                    color="inherit"
                    onClick={() => setCreateOrderOpen(true)}
                  >
                    <CreateChannelIcon />
                  </IconButton>
                </Stack>
                <Divider />
                <Stack sx={styles.phaseSelectContainer}>
                  <PhaseSelect />
                </Stack>
                <Divider />
                <Stack sx={styles.ordersAndButtonContainer}>
                  <QueryContainer
                    query={ordersQuery}
                    onRenderLoading={() => <></>}
                  >
                    {(data) => (
                      <Stack sx={styles.container}>
                        <Stack sx={styles.ordersContainer}>
                          <OrderList orders={data.orders} />
                        </Stack>
                        <Stack sx={styles.actionsContainer}>
                          {data.canConfirmOrders && (
                            <Fab
                              color="secondary"
                              aria-label="confirm orders"
                              onClick={handleToggleConfirmOrders}
                              disabled={isSubmitting}
                              variant="extended"
                            >
                              {data.hasConfirmedOrders ? (
                                <OrdersConfirmedIcon />
                              ) : (
                                <OrdersNotConfirmedIcon />
                              )}
                              {data.hasConfirmedOrders
                                ? "Orders confirmed"
                                : "Confirm orders"}
                            </Fab>
                          )}
                          {data.canCreateOrder && (
                            <Fab
                              sx={styles.fab}
                              color="primary"
                              aria-label="create order"
                              onClick={() => setCreateOrderOpen(true)}
                            >
                              <CreateOrderIcon />
                            </Fab>
                          )}
                        </Stack>
                      </Stack>
                    )}
                  </QueryContainer>
                </Stack>
              </Stack>
            </Stack>
          </Card>
        ) : (
          <Card sx={styles.card} elevation={3}>
            <Stack sx={styles.cardInner}>
              <Stack sx={styles.channelListContainer}>
                <Stack sx={styles.header}>
                  <Typography variant="h2">Conversations</Typography>
                  <IconButton
                    edge="end"
                    color="inherit"
                    onClick={handleCreateChannel}
                  >
                    <CreateChannelIcon />
                  </IconButton>
                </Stack>
                <Divider />
                <ChannelList />
              </Stack>
              <Stack sx={styles.channelContainer}>
                {createChannelOpen ? (
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
      <Modal open={gameInfoOpen}>
        <GameInfo />
      </Modal>
      <Modal open={playerInfoOpen}>
        <PlayerInfo />
      </Modal>
      <Modal open={createOrderOpen}>
        <CreateOrder onClose={() => setCreateOrderOpen(false)} />
      </Modal>
    </Stack>
  );
};

export { GameDetail };
