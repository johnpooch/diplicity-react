# Local development

## Setting environment variables

The service uses environment variables to configure secret settings.

Start by copying the `.env.example` file to a new file named `.env` in the root
of the repository:

```bash
cp .env.example .env
```

```powershell
Copy-Item .env.example .env
```

Then, open the `.env` file and set values for the variables following the
instructions in the file. The `.env` file should not be committed to version
control.

## Linting

The service uses [Flake8](https://flake8.pycqa.org/en/latest/) for linting. It
is recommended that you enable linting on save in your code editor.

**Note**: Linting errors will cause the build to fail in the CI/CD pipeline.

## Running the service

**Note**: The following instructions assume you have Docker and Docker Compose
installed on your machine. If you don't have them installed, please refer to the
[Docker installation guide](https://docs.docker.com/get-docker/) and the [Docker
Compose installation guide](https://docs.docker.com/compose/install/) for
installation instructions.

To run the service locally, run the following command from the root of the
repository:

```bash
docker-compose up diplicity-service diplicity-queue diplicity-worker --build --watch
```

This will build and run the service, queue and worker in a Docker container. The
`--watch` flag will watch for changes in the code and automatically rebuild the
container when changes are detected.

## Running the tests

To run the tests, run the following command from the root of the repository:

```bash
docker-compose up diplicity-test --build --watch
```

This will build and run the tests in a Docker container. The `--watch` flag will
watch for changes in the code and automatically rebuild the container when
changes are detected.
