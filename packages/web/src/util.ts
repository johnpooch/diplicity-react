import { GameRead } from "./store";
import { adjectives, conflictSynonyms, nouns } from "./terms";

function capitalize(s: string) {
  return s.slice(0, 1).toUpperCase() + s.slice(1);
}

function randomOf(ary: string[]) {
  return ary[Math.floor(Math.random() * ary.length)];
}

const getCurrentPhaseId = (game: GameRead) => {
  return game.phases[game.phases.length - 1];
};

function dziemba_levenshtein(a: string, b: string) {
  let tmp;
  if (a.length === 0) {
    return b.length;
  }
  if (b.length === 0) {
    return a.length;
  }
  if (a.length > b.length) {
    tmp = a;
    a = b;
    b = tmp;
  }
  let i,
    j,
    res,
    // eslint-disable-next-line prefer-const
    alen = a.length,
    // eslint-disable-next-line prefer-const
    blen = b.length,
    // eslint-disable-next-line prefer-const
    row = Array(alen);
  for (i = 0; i <= alen; i++) {
    row[i] = i;
  }

  for (i = 1; i <= blen; i++) {
    res = i;
    for (j = 1; j <= alen; j++) {
      tmp = row[j - 1];
      row[j - 1] = res;
      res =
        b[i - 1] === a[j - 1]
          ? tmp
          : Math.min(tmp + 1, Math.min(res + 1, row[j] + 1));
    }
  }
  return res;
}

function funkyFactor(s1: string, s2: string) {
  if (s1.length < 3 || s2.length < 3) {
    return dziemba_levenshtein(s1, s2);
  }
  return (
    dziemba_levenshtein(s1.slice(0, 3), s2.slice(0, 3)) +
    dziemba_levenshtein(s1.slice(-3), s2.slice(-3))
  );
}

function randomOfFunky(basis: string, ary: string[]) {
  const options: { option: string; score: number }[] = [];
  for (let i = 0; i < Math.floor(ary.length / 10); i++) {
    const option = randomOf(ary);
    options.push({
      option: option,
      score: funkyFactor(basis, option),
    });
  }
  options.sort((a, b) => {
    return a.score < b.score ? -1 : 1;
  });
  return options[0].option;
}

export function randomGameName() {
  const synonym = randomOf(conflictSynonyms);
  const adjective = randomOfFunky(synonym, adjectives);
  const noun = randomOfFunky(adjective, nouns);
  return (
    "The " +
    capitalize(synonym) +
    " of the " +
    capitalize(adjective) +
    " " +
    capitalize(noun)
  );
}

/**
 * Formats an order object into a human-readable string.
 */
const formatOrderText = (order: {
  source: string;
  orderType: string;
  target?: string;
  aux?: string;
}) => {
  if (order.orderType === "Hold") {
    return `${order.source} Hold`;
  }
  if (order.orderType === "Support") {
    return `${order.source} Support ${order.target} ${order.aux}`;
  }
  return `${order.source} ${order.orderType} to ${order.target}`;
};

function formatDateTime(djangoDatetime: string) {
  const date = new Date(djangoDatetime);
  const now = new Date();

  // Get dates at midnight for comparison
  const dateAtMidnight = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate()
  );
  const todayAtMidnight = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );
  const tomorrowAtMidnight = new Date(todayAtMidnight);
  tomorrowAtMidnight.setDate(tomorrowAtMidnight.getDate() + 1);

  // Format time as HH:MM
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const timeString = `${hours}:${minutes}`;

  // Check if today or tomorrow
  if (dateAtMidnight.getTime() === todayAtMidnight.getTime()) {
    return `Today ${timeString}`;
  } else if (dateAtMidnight.getTime() === tomorrowAtMidnight.getTime()) {
    return `Tomorrow ${timeString}`;
  } else {
    // Format as DD/MM/YY
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear().toString().slice(-2);
    return `${day}/${month}/${year} ${timeString}`;
  }
}

export { formatOrderText, formatDateTime, getCurrentPhaseId };
