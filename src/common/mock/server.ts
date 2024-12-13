import { createServer, Response } from "miragejs";
import { variant, games } from "../fixtures";

export const makeServer = ({ environment = "test" }) => createServer({
    environment,
    routes() {
        this.namespace = "https://diplicity-engine.appspot.com";

        this.get("https://diplicity-engine.appspot.com/Variants", () => {
            return new Response(200, undefined, {
                Name: "variants",
                Properties: [
                    {
                        Properties: variant
                    }
                ]
            })
        }, { timing: 1000 });

        this.get("https://diplicity-engine.appspot.com/Games/My/Staging", () => {
            return new Response(200, undefined, {
                Name: "games",
                Properties: [
                    { Properties: games.stagingGame1 },
                    { Properties: games.stagingGame2 }
                ]
            });
        }, { timing: 1000 });

        this.get("https://diplicity-engine.appspot.com/Games/My/Started", () => {
            return new Response(200, undefined, {
                Name: "games",
                Properties: [
                    { Properties: games.startedGame1 },
                    { Properties: games.startedGame2 }
                ]
            });
        }, { timing: 1000 });

        this.get("https://diplicity-engine.appspot.com/Games/My/Finished", () => {
            return new Response(200, undefined, {
                Name: "games",
                Properties: [
                    { Properties: games.finishedGame1 },
                    { Properties: games.finishedGame2 }
                ]
            });
        }, { timing: 1000 });

        this.get("https://diplicity-engine.appspot.com/Games/Staging", () => {
            return new Response(200, undefined, {
                Name: "games",
                Properties: [
                    { Properties: games.stagingGame1 },
                    { Properties: games.stagingGame2 }
                ]
            });
        }, { timing: 1000 });
    },
});
