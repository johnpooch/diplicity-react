const label = 'deploy-to-staging';

module.exports = async ({ github, context, core }) => {
  const repository = context.repo;
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    ...repository,
    state: 'open',
    labels: label,
    per_page: 100,
  });

  const latestLabel = async (number) => {
    const events = await github.paginate(github.rest.issues.listEventsForTimeline, {
      ...repository,
      issue_number: number,
      per_page: 100,
    });
    return events.filter(event => event.event === 'labeled' && event.label.name === label)
      .sort((first, second) => second.id - first.id)[0];
  };

  const claims = [];
  for (const issue of issues.filter(issue => issue.pull_request)) {
    const { data: pull } = await github.rest.pulls.get({ ...repository, pull_number: issue.number });
    const event = await latestLabel(pull.number);
    if (!event) throw new Error(`Missing staging label event for PR #${pull.number}`);
    const trusted = pull.head.repo?.full_name === `${repository.owner}/${repository.repo}`;
    if (!trusted) core.info(`Skipping fork PR #${pull.number}; no staging credentials will be used for it.`);
    claims.push({ pull, event, trusted });
  }
  claims.sort((first, second) => second.event.id - first.event.id);

  const claim = claims.find(candidate => candidate.trusted && candidate.pull.state === 'open');
  let target = claim?.pull;
  if (target) {
    const since = claim.event.created_at;
    const runs = await github.paginate(github.rest.actions.listWorkflowRuns, {
      ...repository,
      workflow_id: 'pr-staging.yml',
      created: `>=${since}`,
      per_page: 100,
    });
    const labelTitle = `Staging pull_request labeled ${target.number} true`;
    const requests = runs.filter(run =>
      (run.event === 'push' && run.head_branch === 'main') ||
      run.event === 'workflow_dispatch' ||
      run.display_title === `Staging pull_request synchronize ${target.number} true` ||
      /^Staging pull_request closed \d+ true$/.test(run.display_title) ||
      run.display_title === labelTitle);
    requests.sort((first, second) => second.id - first.id);
    const latest = requests[0];
    const labelRun = requests.find(run => run.display_title === labelTitle && run.created_at >= since);
    if (latest && (latest.event === 'push' || latest.event === 'workflow_dispatch') &&
        (latest.created_at > since || (labelRun && latest.id > labelRun.id))) {
      target = undefined;
    }
  }

  let sha;
  if (target) {
    sha = target.head.sha;
  } else {
    const { data: main } = await github.rest.repos.getBranch({ ...repository, branch: 'main' });
    sha = main.commit.sha;
  }
  if (!/^[a-f0-9]{40}$/.test(sha)) throw new Error('Invalid staging commit SHA');

  core.setOutput('pr', target?.number || '');
  core.setOutput('branch', target?.head.ref || 'main');
  core.setOutput('sha', sha);
  core.info(`Deploying ${target ? `PR #${target.number} (${target.head.ref})` : 'main'} at ${sha}`);

  for (const displaced of claims.filter(candidate => candidate.pull.number !== target?.number)) {
    const current = await latestLabel(displaced.pull.number);
    if (current?.id !== displaced.event.id) continue;
    const { data: pull } = await github.rest.pulls.get({ ...repository, pull_number: displaced.pull.number });
    if (pull.state !== 'open' || !pull.labels.some(currentLabel => currentLabel.name === label)) continue;
    await github.rest.issues.removeLabel({ ...repository, issue_number: pull.number, name: label });
    const destination = target ? `PR #${target.number} (\`${target.head.ref}\`)` : '`main`';
    await github.rest.issues.createComment({
      ...repository,
      issue_number: pull.number,
      body: `Staging moved to ${destination}: https://diplicity-react-staging.up.railway.app. Add the \`${label}\` label again to deploy this PR.`,
    });
  }
};
