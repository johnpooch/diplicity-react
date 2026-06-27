import type {
  Member,
  PublicUserProfile,
  UserProfile,
} from "@/api/generated/endpoints";

export const currentUserProfile: UserProfile = {
  id: 1,
  userId: 1,
  name: "Mock Player",
  picture: null,
  email: "mock.player@example.com",
  emailNotificationsEnabled: true,
  colorblindMode: null,
  canCreateBotGames: false,
};

interface PlayerSeed {
  userId: number;
  name: string;
}

export const players: PlayerSeed[] = [
  { userId: 1, name: "Mock Player" },
  { userId: 2, name: "Alice" },
  { userId: 3, name: "Bob" },
  { userId: 4, name: "Charlie" },
  { userId: 5, name: "Diana" },
  { userId: 6, name: "Eve" },
  { userId: 7, name: "Frank" },
];

let memberIdCounter = 0;

export const makeMember = (
  player: PlayerSeed,
  nation: string | null,
  overrides: Partial<Member> = {}
): Member => ({
  id: ++memberIdCounter,
  userId: player.userId,
  name: player.name,
  picture: null,
  isCurrentUser: player.userId === currentUserProfile.userId,
  nation,
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 2,
  civilDisorder: false,
  seekingReplacement: false,
  replaceable: false,
  ...overrides,
});

export const publicProfiles: Record<number, PublicUserProfile> = {};

for (const player of players) {
  publicProfiles[player.userId] = {
    id: player.userId,
    name: player.name,
    picture: null,
    createdAt: "2025-01-15T12:00:00Z",
    totalGames: 12,
    soloWins: 1,
    draws: 3,
    losses: 6,
    nmrRate: 0.05,
    cdRate: 0,
    reliabilityTier: "reliable",
  };
}
