Analyze and create an implementation plan to address PR review feedback.

## Arguments

The argument should be a PR number or URL. Examples:
- `124`
- `https://github.com/johnpooch/diplicity-react/pull/124`

PR reference: $ARGUMENTS

## Instructions

1. **Fetch Unresolved PR Review Comments**
   - Use the GraphQL API to fetch only unresolved review threads:
     ```bash
     gh api graphql -f query='
       query($owner: String!, $repo: String!, $pr: Int!) {
         repository(owner: $owner, name: $repo) {
           pullRequest(number: $pr) {
             reviewThreads(first: 100) {
               nodes {
                 isResolved
                 id
                 comments(first: 10) {
                   nodes {
                     body
                     path
                     line
                   }
                 }
               }
             }
           }
         }
       }
     ' -f owner='{owner}' -f repo='{repo}' -F pr={pr_number}
     ```
   - Filter to only include threads where `isResolved` is `false`
   - Extract the comment body, file path, line number, and thread ID for each unresolved comment
   - If all comments are resolved, report this to the user and stop

2. **Read Affected Files**
   - For each unique file path mentioned in the comments, read that file to understand the current implementation

3. **Analyze Each Comment**
   - For each review comment, determine:
     - What concern is being raised?
     - What is the current state of the code?
     - What change is being requested or suggested?
     - Is the reviewer's concern valid based on project patterns in CLAUDE.md?
     - What is the recommended action (agree, partially agree, disagree with reasoning)?

4. **Create Implementation Plan**
   - Summarize all review comments in a table format:
     | # | Comment | File | Line |
     |---|---------|------|------|
   - For each comment, provide:
     - Analysis of the concern
     - Evidence from the codebase supporting your recommendation
     - Specific code changes needed (if any)
   - List all files that will be modified
   - Include verification steps (tests to run, linting, etc.)

5. **Enter Plan Mode**
   - Use EnterPlanMode to present the implementation plan for user approval
   - The plan should be detailed enough that it can be implemented directly after approval

6. **After Implementation**
   - Once all changes are implemented and verified (tests pass, lint passes), push the changes to the remote branch
   - Use `git push` to push the changes so the user can review them on GitHub
   - Resolve each addressed review thread using the GraphQL API:
     ```bash
     gh api graphql -f query='
       mutation($threadId: ID!) {
         resolveReviewThread(input: {threadId: $threadId}) {
           thread {
             isResolved
           }
         }
       }
     ' -f threadId='{thread_id}'
     ```
   - Run this for each thread ID that was addressed in the implementation

## Important Notes

- Always provide evidence-based reasoning for each recommendation
- Reference specific patterns from CLAUDE.md when relevant
- If you disagree with a review comment, explain why with concrete evidence
- Include CLAUDE.md updates if the review reveals undocumented patterns
