import React from "react";
import { Navigate, Route, Routes } from "react-router";
import { useSelector } from "react-redux";
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
  Panel,
  Channel,
  ChannelTextField,
  ChannelList,
  Map,
  CreateChannel,
  CreateChannelAction,
  CreateChannelTextField,
  GameMenu,
  OrderList,
  QueryContainer,
} from "./components";
import { PhaseSelect } from "./components/phase-select";
import { GameName } from "./components/game-detail/game-name";
import {
  CreateChannelContextProvider,
  CreateOrderContextProvider,
  SelectedChannelContextProvider,
  SelectedGameContextProvider,
} from "./context";
import { CreateOrder } from "./components/orders/create-order";
import { selectAuth } from "./store";

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
            <SelectedGameContextProvider>
              {({ gameRetrieveQuery }) => (
                <Desktop.HomeSecondaryScreenLayout
                  title="Game info"
                  onNavigateBack={(navigate) => navigate("/")}
                  secondaryAction={
                    <QueryContainer
                      query={gameRetrieveQuery}
                      onRenderLoading={() => <> </>}
                    >
                      {(game) => (
                        <GameMenu
                          game={game}
                          onClickGameInfo={(navigate) =>
                            navigate(`/game-info/${game.id}`)
                          }
                          onClickPlayerInfo={(navigate) =>
                            navigate(`/player-info/${game.id}`)
                          }
                        />
                      )}
                    </QueryContainer>
                  }
                />
              )}
            </SelectedGameContextProvider>
          }
        >
          <Route index element={<GameInfo />} />
        </Route>
        <Route
          path="player-info/:gameId"
          element={
            <SelectedGameContextProvider>
              {({ gameRetrieveQuery }) => (
                <Desktop.HomeSecondaryScreenLayout
                  title="Player info"
                  secondaryAction={
                    <QueryContainer
                      query={gameRetrieveQuery}
                      onRenderLoading={() => <> </>}
                    >
                      {(game) => (
                        <GameMenu
                          game={game}
                          onClickGameInfo={(navigate) =>
                            navigate(`/game-info/${game.id}`)
                          }
                          onClickPlayerInfo={(navigate) =>
                            navigate(`/player-info/${game.id}`)
                          }
                        />
                      )}
                    </QueryContainer>
                  }
                  onNavigateBack={(navigate) => navigate("/")}
                />
              )}
            </SelectedGameContextProvider>
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
                  </Panel>
                }
              />
              <Route
                path="orders"
                element={
                  <CreateOrderContextProvider>
                    {(source) => (
                      <Panel>
                        <Panel.Content>
                          <OrderList />
                        </Panel.Content>
                        {source && (
                          <Panel.Footer divider>
                            <CreateOrder />
                          </Panel.Footer>
                        )}
                      </Panel>
                    )}
                  </CreateOrderContextProvider>
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
                        <CreateChannelTextField />
                      </Panel.Footer>
                    </Panel>
                  </CreateChannelContextProvider>
                }
              />
            </Route>
            <Route
              element={
                <SelectedChannelContextProvider>
                  <Mobile.GameDetailSecondaryScreenLayout
                    title="Channel"
                    onNavigateBack={(navigate, gameId) =>
                      navigate(`/game/${gameId}/chat`)
                    }
                  />
                </SelectedChannelContextProvider>
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
                  <CreateOrderContextProvider>
                    {(source) => (
                      <Panel>
                        <Panel.Content>
                          <OrderList />
                        </Panel.Content>
                        {source && (
                          <Panel.Footer divider>
                            <CreateOrder />
                          </Panel.Footer>
                        )}
                      </Panel>
                    )}
                  </CreateOrderContextProvider>
                }
              />
              <Route
                path="orders"
                element={
                  <CreateOrderContextProvider>
                    {(source) => (
                      <Panel>
                        <Panel.Content>
                          <OrderList />
                        </Panel.Content>
                        {source && (
                          <Panel.Footer divider>
                            <CreateOrder />
                          </Panel.Footer>
                        )}
                      </Panel>
                    )}
                  </CreateOrderContextProvider>
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
                      {/* <Panel.Footer>
                        <CreateChannelTextField />
                      </Panel.Footer> */}
                    </Panel>
                  </CreateChannelContextProvider>
                }
              />
            </Route>
            <Route
              element={
                <SelectedChannelContextProvider>
                  <Desktop.GameDetailSecondaryScreenLayout
                    title="Channel"
                    onNavigateBack={(navigate, gameId) =>
                      navigate(`/game/${gameId}/chat`)
                    }
                  />
                </SelectedChannelContextProvider>
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
