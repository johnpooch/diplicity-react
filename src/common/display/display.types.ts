type GameMember = {
    id: string;
    username: string;
    src: string;
    nation?: string;
    stats: UserStats;
}

type UserStats = {
    consistency: string;
    rank: string;
    numPlayed: number;
    numWon: number;
    numDrawn: number;
    numAbandoned: number;
}

type Phase = {
    year: number;
    season: string;
    type: string;
    duration: string;
    remaining: string;
}

type Variant = {
    name: string;
    author: string;
    startYear: number;
    numPlayers: number;
    winCondition: string;
}

type Game = {
    id: string;
    title: string;
    user?: GameMember;
    users: GameMember[];
    status: "staging" | "started" | "finished";
    private: boolean;
    userCanJoin: boolean;
    userCanLeave: boolean;
    movementPhaseDuration: string;
    nonMovementPhaseDuration: string;
    currentPhase?: Phase;
    minCommitment?: string;
    minRank?: string;
    maxRank?: string;
    language: string;
    variant: Variant;
}

type GameDetail = Game & {
}

export type { Game, GameDetail, GameMember };