import React from "react";
import { Navigate, Route, Routes } from "react-router";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import {
  CreateGame,
  FindGames,
  GameInfo,
  HomeLayout,
  MyGames,
  PlayerInfo,
  Profile,
  Login,
} from "./screens";
import { Stack, useMediaQuery, useTheme } from "@mui/material";
import { ParseMap } from "./screens/parse-map";
import * as Desktop from "./screens/desktop";
import * as Mobile from "./screens/mobile";
import {
  CreateOrder,
  OrderActions,
  OrderList,
  Panel,
  Channel,
  ChannelTextField,
  ChannelList,
  Map,
  CreateChannel,
  CreateChannelAction,
  CreateChannelTetxField,
  CreateChannelContextProvider,
} from "./components";
import { ChannelContextProvider } from "./context/channel-context";
import { PhaseSelect } from "./components/phase-select";
import { GameName } from "./components/game-detail/game-name";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  return loggedIn ? (
    <Routes>
      <Route path="/parse-map" element={<ParseMap />} />
      <Route element={<HomeLayout />}>
        <Route index element={<MyGames />} />
        <Route
          path="find-games"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Find games"
              onNavigateBack={(navigate) => navigate("/")}
            />
          }
        >
          <Route index element={<FindGames />} />
        </Route>
        <Route
          path="create-game"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Create game"
              onNavigateBack={(navigate) => navigate("/")}
            />
          }
        >
          <Route index element={<CreateGame />} />
        </Route>
        <Route
          path="profile"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Profile"
              onNavigateBack={(navigate) => navigate("/")}
            />
          }
        >
          <Route index element={<Profile />} />
        </Route>
        <Route
          path="game-info/:gameId"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Game info"
              onNavigateBack={(navigate) => navigate("/")}
            />
          }
        >
          <Route index element={<GameInfo />} />
        </Route>
        <Route
          path="player-info/:gameId"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Player info"
              onNavigateBack={(navigate) => navigate("/")}
            />
          }
        >
          <Route index element={<PlayerInfo />} />
        </Route>
      </Route>
      {isMobile ? (
        <Route path="game/:gameId">
          <Route element={<Mobile.GameDetailLayout />}>
            <Route
              element={
                <Mobile.GameDetailPrimaryScreenLayout
                  title={
                    <Stack sx={{ width: "100%", alignItems: "center" }}>
                      <PhaseSelect />
                    </Stack>
                  }
                />
              }
            >
              <Route
                index
                element={
                  <Panel>
                    <Panel.Content>
                      <Map />
                    </Panel.Content>
                    <Panel.Footer>
                      <OrderActions />
                    </Panel.Footer>
                  </Panel>
                }
              />
              <Route
                path="orders"
                element={
                  <Panel>
                    <Panel.Content>
                      <OrderList />
                    </Panel.Content>
                    <Panel.Footer>
                      <OrderActions />
                    </Panel.Footer>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={<Mobile.GameDetailPrimaryScreenLayout title="Chat" />}
            >
              <Route
                path="chat"
                element={
                  <Panel>
                    <Panel.Content>
                      <ChannelList />
                    </Panel.Content>
                    <Panel.Footer>
                      <CreateChannelAction />
                    </Panel.Footer>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Mobile.GameDetailSecondaryScreenLayout
                  title="Create order"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="orders/create"
                element={
                  <Panel>
                    <Panel.Content>
                      <CreateOrder />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Mobile.GameDetailSecondaryScreenLayout
                  title="Game info"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="game-info"
                element={
                  <Panel>
                    <Panel.Content>
                      <GameInfo />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Mobile.GameDetailSecondaryScreenLayout
                  title="Player info"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="player-info"
                element={
                  <Panel>
                    <Panel.Content>
                      <PlayerInfo />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Mobile.GameDetailSecondaryScreenLayout
                  title="Create channel"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}/chat`)
                  }
                />
              }
            >
              <Route
                path="chat/channel/create"
                element={
                  <CreateChannelContextProvider>
                    <Panel>
                      <Panel.Content>
                        <CreateChannel />
                      </Panel.Content>
                      <Panel.Footer>
                        <CreateChannelTetxField />
                      </Panel.Footer>
                    </Panel>
                  </CreateChannelContextProvider>
                }
              />
            </Route>
            <Route
              element={
                <ChannelContextProvider>
                  <Mobile.GameDetailSecondaryScreenLayout
                    title="Channel"
                    onNavigateBack={(navigate, gameId) =>
                      navigate(`/game/${gameId}/chat`)
                    }
                  />
                </ChannelContextProvider>
              }
            >
              <Route
                path="chat/channel/:channelName"
                element={
                  <Panel>
                    <Panel.Content>
                      <Channel />
                    </Panel.Content>
                    <Panel.Footer>
                      <ChannelTextField />
                    </Panel.Footer>
                  </Panel>
                }
              />
            </Route>
          </Route>
        </Route>
      ) : (
        <Route path="game/:gameId">
          <Route element={<Desktop.GameDetailLayout title={<GameName />} />}>
            <Route element={<Desktop.GameDetailPrimaryScreenLayout />}>
              <Route
                index
                element={
                  <Panel>
                    <Panel.Content>
                      <OrderList />
                    </Panel.Content>
                    <Panel.Footer>
                      <OrderActions />
                    </Panel.Footer>
                  </Panel>
                }
              />
              <Route
                path="orders"
                element={
                  <Panel>
                    <Panel.Content>
                      <OrderList />
                    </Panel.Content>
                    <Panel.Footer>
                      <OrderActions />
                    </Panel.Footer>
                  </Panel>
                }
              />
              <Route
                path="chat"
                element={
                  <Panel>
                    <Panel.Content>
                      <ChannelList />
                    </Panel.Content>
                    <Panel.Footer>
                      <CreateChannelAction />
                    </Panel.Footer>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Desktop.GameDetailSecondaryScreenLayout
                  title="Create order"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="orders/create"
                element={
                  <Panel>
                    <Panel.Content>
                      <CreateOrder />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Desktop.GameDetailSecondaryScreenLayout
                  title="Game info"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="game-info"
                element={
                  <Panel>
                    <Panel.Content>
                      <GameInfo />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Desktop.GameDetailSecondaryScreenLayout
                  title="Player info"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}`)
                  }
                />
              }
            >
              <Route
                path="player-info"
                element={
                  <Panel>
                    <Panel.Content>
                      <PlayerInfo />
                    </Panel.Content>
                  </Panel>
                }
              />
            </Route>
            <Route
              element={
                <Desktop.GameDetailSecondaryScreenLayout
                  title="Create channel"
                  onNavigateBack={(navigate, gameId) =>
                    navigate(`/game/${gameId}/chat`)
                  }
                />
              }
            >
              <Route
                path="chat/channel/create"
                element={
                  <CreateChannelContextProvider>
                    <Panel>
                      <Panel.Content>
                        <CreateChannel />
                      </Panel.Content>
                      <Panel.Footer>
                        <CreateChannelTetxField />
                      </Panel.Footer>
                    </Panel>
                  </CreateChannelContextProvider>
                }
              />
            </Route>
            <Route
              element={
                <ChannelContextProvider>
                  <Desktop.GameDetailSecondaryScreenLayout
                    title="Channel"
                    onNavigateBack={(navigate, gameId) =>
                      navigate(`/game/${gameId}/chat`)
                    }
                  />
                </ChannelContextProvider>
              }
            >
              <Route
                path="chat/channel/:channelName"
                element={
                  <Panel>
                    <Panel.Content>
                      <Channel />
                    </Panel.Content>
                    <Panel.Footer>
                      <ChannelTextField />
                    </Panel.Footer>
                  </Panel>
                }
              />
            </Route>
          </Route>
        </Route>
      )}
    </Routes>
  ) : (
    <Routes>
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/" element={<Login />} />
    </Routes>
  );
};

export default Router;
