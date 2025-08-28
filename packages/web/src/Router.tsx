import React from "react";
import { Navigate, Outlet, Route, Routes } from "react-router";
import { useSelector } from "react-redux";
import { Login } from "./screens";
import { MyGames as NewMyGames } from "./components/screens/MyGames";
import { FindGames as NewFindGames } from "./components/screens/FindGames";
import { CreateGame as NewCreateGame } from "./components/screens/CreateGame";
import { Profile as NewProfile } from "./components/screens/Profile";
import { GameInfo as NewGameInfo } from "./components/screens/GameInfo";
import { PlayerInfo as NewPlayerInfo } from "./components/screens/PlayerInfo";
import { selectAuth } from "./store";
import { SelectedGameContextProvider, SelectedPhaseContextProvider } from "./context";
import { GameDetail } from "./components/screens";
import { ChannelCreateScreen } from "./components/screens/GameDetail/ChannelCreateScreen";
import { ChannelScreen } from "./components/screens/GameDetail/ChannelScreen";
import { useResponsiveness } from "./components/utils/responsive";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const responsiveness = useResponsiveness();

  return loggedIn ? (
    <Routes>
      <Route index element={<NewMyGames />} />
      <Route path="/find-games" element={<NewFindGames />} />
      <Route path="/create-game" element={<NewCreateGame />} />
      <Route path="/profile" element={<NewProfile />} />
      <Route path="/game-info/:gameId" element={<NewGameInfo />} />
      <Route path="/player-info/:gameId" element={<NewPlayerInfo />} />
      <Route path="/game/:gameId" element={
        <SelectedGameContextProvider>
          <SelectedPhaseContextProvider>
            <Outlet />
          </SelectedPhaseContextProvider>
        </SelectedGameContextProvider>
      }>
        <Route
          path=""
          element={responsiveness.device === "mobile" ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />}
        />
        <Route
          path="orders"
          element={<GameDetail.OrdersScreen />}
        />
        <Route
          path="chat"
          element={<GameDetail.ChannelListScreen />}
        />
        <Route
          path="chat/channel/create"
          element={<ChannelCreateScreen />}
        />
        <Route
          path="chat/channel/:channelId"
          element={<ChannelScreen />}
        />
      </Route>
      {
        responsiveness.device === "mobile" ? (
          <>
            {/* <Route path="/game/:gameId" element={<GameDetail panel="orders" />} />
          <Route path="/game/:gameId" element={<GameDetail panel="orders" />} /> */}
          </>
        ) : (
          <>
            {/* Use layout approach for desktop - move map to the right and otherwise make it the same as mobile */}
            {/* <Route path="/game/:gameId" element={<GameDetail panel="orders" />} /> */}
            {/* <Route
            path="/game/:gameId/orders"
            element={<GameDetail panel="orders" />}
          />
          <Route
            path="/game/:gameId/chat"
            element={<GameDetail panel="chat" />}
          /> */}
          </>
        )
      }
      {/* <Route element={<HomeLayout />}>
        <Route index element={<MyGames />} />
        <Route
          path="find-games"
          element={
            <Desktop.HomeSecondaryScreenLayout
              title="Find games"
              onNavigateBack={navigate => navigate("/")}
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
              onNavigateBack={navigate => navigate("/")}
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
              onNavigateBack={navigate => navigate("/")}
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
                  onNavigateBack={navigate => navigate("/")}
                  secondaryAction={
                    <QueryContainer
                      query={gameRetrieveQuery}
                      onRenderLoading={() => <> </>}
                    >
                      {game => (
                        <GameMenu
                          game={game}
                          onClickGameInfo={navigate =>
                            navigate(`/game-info/${game.id}`)
                          }
                          onClickPlayerInfo={navigate =>
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
                      {game => (
                        <GameMenu
                          game={game}
                          onClickGameInfo={navigate =>
                            navigate(`/game-info/${game.id}`)
                          }
                          onClickPlayerInfo={navigate =>
                            navigate(`/player-info/${game.id}`)
                          }
                        />
                      )}
                    </QueryContainer>
                  }
                  onNavigateBack={navigate => navigate("/")}
                />
              )}
            </SelectedGameContextProvider>
          }
        >
          <Route index element={<PlayerInfo />} />
        </Route>
      </Route> */}
      {/* {isMobile ? (
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
                    <Panel>
                      <Panel.Content>
                        <OrderList />
                      </Panel.Content>
                    </Panel>
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
                    <Panel>
                      <Panel.Content>
                        <OrderList />
                      </Panel.Content>
                    </Panel>
                  </CreateOrderContextProvider>
                }
              />
              <Route
                path="orders"
                element={
                  <CreateOrderContextProvider>
                    <Panel>
                      <Panel.Content>
                        <OrderList />
                      </Panel.Content>
                    </Panel>
                  </CreateOrderContextProvider>
                }
              />
              <Route path="chat" element={<ChannelList />} />
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
                    <CreateChannel />
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
      )} */}
    </Routes >
  ) : (
    <Routes>
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/" element={<Login />} />
    </Routes>
  );
};

export default Router;
