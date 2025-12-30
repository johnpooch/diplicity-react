# Frontend Refactor

I recently added new versions of a number of screens. These screens are built on top of Tailwind and ShadCN. They replace previous versions of the screens which are built on top of Material UI.o

I want to do a bit of cleanup and refactoring on these screens, extracting common patterns into reusable components, etc.

## Proposed Changes

- Add `ScreenCard` component and related components (e.g. `ScreenCardContent`, `ScreenCardHeader`, etc.). These would be wrappers around the `Card` component and related components (e.g. `CardContent`). They would apply styles to make the "card" section of each screen always follow the correct pattern. The `ScreenCard` and related components would be used on `CreateGame.new`, `GameInfo.new`, `PlayerInfo.new`, and `Profile.new`.

- Add `GameDropdownMenu` component which is the dropdown menu that currently appears on the `GameCard.new`, `GameInfo.new` and `PlayerInfo.new` screens.

- Add `JoinLeaveGameButton` component which encapsulates the behaviour around determining when to render the join/leave game button and the rendering logic itself. Importantly, this should take a `game` property that only includes the fields that are needed by the component. This way, both the GameRetrieve and GameList types will work.

- Extract `MetadataRow` from `GameInfo.new` and reuse in `CreateGame.new`.

- Add `ScreenHeader` component that provides consistent layout for page headers with title and optional action buttons. This would standardize the header pattern used across `GameInfo.new`, `PlayerInfo.new`, `Profile.new`, `MyGames.new`, `FindGames.new`, `SandboxGames.new`, and `CreateGame.new`.

- Add `GameStatusAlerts` component that displays game status alerts (pending game notice and victory announcement). This component is currently duplicated identically in `GameInfo.new` and `PlayerInfo.new`. It should take `game` and `variant` props to determine which alerts to show.

