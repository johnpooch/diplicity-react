const assert = require('node:assert/strict');
const test = require('node:test');
const resolveTarget = require('./staging-target.cjs');

const mainSha = 'a'.repeat(40);
const firstSha = 'b'.repeat(40);
const secondSha = 'c'.repeat(40);

function pull(number, options = {}) {
  return {
    number,
    state: 'open',
    labels: [{ name: 'deploy-to-staging' }],
    head: { sha: firstSha, ref: `pr-${number}`, repo: { full_name: 'johnpooch/diplicity-react' } },
    ...options,
  };
}

function labelEvent(id, createdAt = '2026-10-26T12:00:00Z') {
  return { id, created_at: createdAt, event: 'labeled', label: { name: 'deploy-to-staging' } };
}

function run(id, event, createdAt, number = 0, action = 'deploy') {
  return {
    id,
    event,
    created_at: createdAt,
    head_branch: 'main',
    display_title: `Staging ${event} ${action} ${number} ${event === 'pull_request' && action !== 'ignored'}`,
  };
}

async function resolve({ pulls = [], events = {}, runs = [], advance, main = mainSha } = {}) {
  const outputs = {};
  const removed = [];
  const comments = [];
  const logs = [];
  const reads = [];
  const timelineReads = new Map();
  const github = {
    rest: {
      issues: {
        listForRepo: 'issues',
        listEventsForTimeline: 'timeline',
        removeLabel: async request => removed.push(request.issue_number),
        createComment: async request => comments.push(request),
      },
      actions: { listWorkflowRuns: 'runs' },
      pulls: { get: async request => ({ data: pulls.find(candidate => candidate.number === request.pull_number) }) },
      repos: { getBranch: async () => ({ data: { commit: { sha: main } } }) },
    },
    paginate: async (method, request) => {
      reads.push({ method, request });
      if (method === 'issues') return pulls.map(candidate => ({ number: candidate.number, pull_request: {} }));
      if (method === 'timeline') {
        const count = (timelineReads.get(request.issue_number) || 0) + 1;
        timelineReads.set(request.issue_number, count);
        return advance?.(request.issue_number, count) || events[request.issue_number] || [];
      }
      if (method === 'runs') return runs.filter(candidate => candidate.created_at >= request.created.slice(2));
      throw new Error(`Unexpected pagination: ${method}`);
    },
  };
  const context = { repo: { owner: 'johnpooch', repo: 'diplicity-react' } };
  const core = { setOutput: (name, value) => { outputs[name] = value; }, info: message => logs.push(message) };
  await resolveTarget({ github, context, core });
  return { outputs, removed, comments, logs, reads };
}

test('an unclaimed environment deploys the current main SHA', async () => {
  const result = await resolve();
  assert.deepEqual(result.outputs, { pr: '', branch: 'main', sha: mainSha });
  assert.deepEqual(result.removed, []);
});

test('a labelled PR deploys its head rather than a merge commit', async () => {
  const result = await resolve({ pulls: [pull(1)], events: { 1: [labelEvent(10)] } });
  assert.deepEqual(result.outputs, { pr: 1, branch: 'pr-1', sha: firstSha });
  assert.deepEqual(result.removed, []);
});

test('the latest label wins even when an older labelled run starts last', async () => {
  const result = await resolve({
    pulls: [pull(1), pull(2, { head: { ...pull(2).head, sha: secondSha } })],
    events: { 1: [labelEvent(10)], 2: [labelEvent(20)] },
  });
  assert.equal(result.outputs.pr, 2);
  assert.equal(result.outputs.sha, secondSha);
  assert.deepEqual(result.removed, [1]);
  assert.match(result.comments[0].body, /Staging moved to PR #2/);
});

test('relabeling A after B chooses A within the same second', async () => {
  const result = await resolve({
    pulls: [pull(1), pull(2)],
    events: { 1: [labelEvent(10), labelEvent(30)], 2: [labelEvent(20)] },
  });
  assert.equal(result.outputs.pr, 1);
  assert.deepEqual(result.removed, [2]);
});

test('a push to main displaces every open labelled PR', async () => {
  const result = await resolve({
    pulls: [pull(1), pull(2)],
    events: { 1: [labelEvent(10)], 2: [labelEvent(20)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z')],
  });
  assert.equal(result.outputs.branch, 'main');
  assert.deepEqual(result.removed, [2, 1]);
  assert.equal(result.comments.length, 2);
  assert.match(result.comments[0].body, /Staging moved to `main`/);
});

test('manual recovery displaces labelled PRs even from a non-main workflow ref', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [{ ...run(100, 'workflow_dispatch', '2026-10-26T12:00:01Z'), head_branch: 'workflow-test' }],
  });
  assert.deepEqual(result.outputs, { pr: '', branch: 'main', sha: mainSha });
  assert.deepEqual(result.removed, [1]);
});

test('a label after a queued main push wins', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10, '2026-10-26T12:00:02Z')] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z')],
  });
  assert.equal(result.outputs.pr, 1);
});

test('a same-second main push after the label wins by run ID', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [run(101, 'push', '2026-10-26T12:00:00Z'), run(100, 'pull_request', '2026-10-26T12:00:00Z', 1, 'labeled')],
  });
  assert.equal(result.outputs.branch, 'main');
});

test('a same-second label after the main push wins by run ID', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [run(100, 'push', '2026-10-26T12:00:00Z'), run(101, 'pull_request', '2026-10-26T12:00:00Z', 1, 'labeled')],
  });
  assert.equal(result.outputs.pr, 1);
});

test('a holder push after a queued main request wins without relabeling', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z'), run(101, 'pull_request', '2026-10-26T12:00:02Z', 1, 'synchronize')],
  });
  assert.equal(result.outputs.pr, 1);
});

test('a push to another PR cannot override a main request', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z'), run(101, 'pull_request', '2026-10-26T12:00:02Z', 2, 'synchronize')],
  });
  assert.equal(result.outputs.branch, 'main');
});

test('unrelated label changes cannot override a main request', async () => {
  const result = await resolve({
    pulls: [pull(1)], events: { 1: [labelEvent(10)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z'), run(101, 'pull_request', '2026-10-26T12:00:02Z', 1, 'ignored')],
  });
  assert.equal(result.outputs.branch, 'main');
});

test('a closed holder is not checked out when no open labels remain', async () => {
  const result = await resolve();
  assert.equal(result.outputs.branch, 'main');
  assert.equal(result.outputs.pr, '');
});

test('another labelled open PR takes over when the holder has closed', async () => {
  const result = await resolve({ pulls: [pull(2)], events: { 2: [labelEvent(20)] } });
  assert.equal(result.outputs.pr, 2);
});

test('closing the holder after a queued main request falls back to another labelled PR', async () => {
  const result = await resolve({
    pulls: [pull(2)], events: { 2: [labelEvent(20)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z'), run(101, 'pull_request', '2026-10-26T12:00:02Z', 1, 'closed')],
  });
  assert.equal(result.outputs.pr, 2);
});

test('closing an unlabelled PR does not override a queued main request', async () => {
  const closed = run(101, 'pull_request', '2026-10-26T12:00:02Z', 1, 'closed');
  closed.display_title = 'Staging pull_request closed 1 false';
  const result = await resolve({
    pulls: [pull(2)], events: { 2: [labelEvent(20)] },
    runs: [run(100, 'push', '2026-10-26T12:00:01Z'), closed],
  });
  assert.equal(result.outputs.branch, 'main');
});

test('fork labels are never selected and are removed when main takes over', async () => {
  const fork = pull(1, { head: { ...pull(1).head, repo: { full_name: 'outsider/diplicity-react' } } });
  const result = await resolve({ pulls: [fork], events: { 1: [labelEvent(10)] } });
  assert.equal(result.outputs.branch, 'main');
  assert.deepEqual(result.removed, [1]);
  assert.match(result.logs[0], /Skipping fork PR/);
});

test('a fork cannot displace a same-repository PR', async () => {
  const fork = pull(2, { head: { ...pull(2).head, repo: { full_name: 'outsider/diplicity-react' } } });
  const result = await resolve({ pulls: [pull(1), fork], events: { 1: [labelEvent(10)], 2: [labelEvent(20)] } });
  assert.equal(result.outputs.pr, 1);
  assert.deepEqual(result.removed, [2]);
});

test('a new claim arriving during cleanup keeps its label for the queued run', async () => {
  const result = await resolve({
    pulls: [pull(1), pull(2)], events: { 1: [labelEvent(10)], 2: [labelEvent(20)] },
    advance: (number, count) => number === 1 && count > 1 ? [labelEvent(30)] : undefined,
  });
  assert.equal(result.outputs.pr, 2);
  assert.deepEqual(result.removed, []);
});

test('a missing label timeline is an error rather than an arbitrary deployment', async () => {
  await assert.rejects(resolve({ pulls: [pull(1)] }), /Missing staging label event/);
});

test('an invalid SHA is rejected before checking out a target', async () => {
  await assert.rejects(resolve({ main: 'not-a-sha' }), /Invalid staging commit SHA/);
});
