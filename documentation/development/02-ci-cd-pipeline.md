# CI/CD Pipeline

## Overview

We use GitHub Actions for our CI/CD pipeline. The pipeline is defined in the
`.github/workflows` directory of the repository.

Pull requests into the `main` branch will trigger the pipeline to run. The
pipeline will run the following steps:

1. **Linting**: The pipeline will run Flake8 to check for linting errors. If any
   errors are found, the pipeline will fail.
2. **Testing**: The pipeline will run the tests. If any tests fail,
   the pipeline will fail.
3. **Build**: The pipeline will build the Docker image for the service and the
   task queue.
4. **Test tasks**: The pipeline will complete an automated end-to-end test of
   the task workflow.

Changes to the `main` branch will trigger the pipeline to run. The pipeline will
run the same steps as for pull requests, but it will also deploy the service to
Azure if all steps pass.
