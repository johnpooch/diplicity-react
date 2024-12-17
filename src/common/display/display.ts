import { Display } from ".";
import { Service } from "../store";
import { Variant } from "../store/service.types";

const convertMinutesToDisplayString = (minutes: number): string => {
    if (minutes < 0) return "0m";
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes === 0 ? `${hours}h` : `${hours}h ${remainingMinutes}m`;
}

const createGameDisplay = (game: Service.Game, variants: Service.Variant[], user: Service.User): Display.Game => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const variant = variants.find((variant) => variant.Name === game.Variant) as Variant;
    const userMember = game.Members.find((member) => member.User.Id === user.Id);

    const userCanJoin = Boolean(!game.Started && !game.Finished && !userMember);
    const userCanLeave = Boolean(game.Started && !game.Finished && userMember);

    const currentPhase = game.NewestPhaseMeta ? {
        year: game.NewestPhaseMeta[0].Year,
        season: game.NewestPhaseMeta[0].Season,
        type: game.NewestPhaseMeta[0].Type,
        duration: `${game.PhaseLengthMinutes} minutes`,
        remaining: convertMinutesToDisplayString(game.NewestPhaseMeta[0].NextDeadlineIn),
    } : undefined;

    return {
        id: game.ID,
        title: game.Desc,
        user: userMember && {
            id: userMember.User.Id,
            username: userMember.User.Name,
            src: userMember.User.Picture,
            nation: userMember.Nation,
            stats: {
                consistency: "Consistent",
                rank: "Private first class",
                numPlayed: 10,
                numWon: 5,
                numDrawn: 3,
                numAbandoned: 2,
            }
        },
        users: game.Members.map((member) => ({
            id: member.User.Id,
            username: member.User.Name,
            src: member.User.Picture,
            nation: member.Nation,
            stats: {
                consistency: "Consistent",
                rank: "Private first class",
                numPlayed: 10,
                numWon: 5,
                numDrawn: 3,
                numAbandoned: 2,
            }
        })),
        status: game.Finished ? "finished" : game.Started ? "started" : "staging",
        private: game.Private,
        userCanJoin,
        userCanLeave,
        movementPhaseDuration: convertMinutesToDisplayString(game.PhaseLengthMinutes),
        nonMovementPhaseDuration: convertMinutesToDisplayString(game.NonMovementPhaseLengthMinutes),
        currentPhase,
        minCommitment: game.MinReliability.toString(),
        minRank: game.MinRating.toString(),
        maxRank: game.MaxRating.toString(),
        language: game.ChatLanguageISO639_1,
        variant: {
            name: variant.Name,
            author: variant.CreatedBy,
            startYear: variant.Start.Year,
            numPlayers: variant.Nations.length,
            winCondition: variant.Rules,
        }
    }
};

export { createGameDisplay };