# Claude

## Style Guide

### General

- **Comments**: Do not add docstrings or comments.

### Project Structure

The project is broken down into apps, where each app is reponsible for a single core concept, e.g. `game`, `order`, `user_profile`, etc.

Apps must adhere to the following guidelines:

**Views**

Views should be simple and should leverage DRF generic views where appropriate. The `check_permissions` method should be used to carry out initial permission checks for the request. Mixins should be used to provide context to the views and serializers.

**Serializers**

Serializers should use the standard `Serializer` base class over the `ModelSerializer` base class. They should be kept as simple as possible.

**Models**

Models have two responsibilities: (1) defining the fields of the data structure; (2) defining properties for conveniently accessing related entities and deriving data.

Query optimization code should be defined on a custom QuerySet class.

**Testing**

Test fixtures should be exist in the app's `conftest.py` file rather than in the test file itself.

For most apps, testing the API endpoints is sufficient. Tests should comprehensively cover the behaviour of the endpoints. Performance tests should be added to ensure that N+1 query issues are avoided.

For complex logic, e.g. logic that exists in util files, separate test classes should be added.

**Utils**

Logic which does not naturally belong in the serializers, views, or models should be defined in the `utils.py` file.

## Testing

To run all backend tests:
```bash
docker compose run --rm service python3 -m pytest -v
```

To run a specific test file:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py -v
```

To run a specific test function:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::test_create_game_success -v 
```

To run a specific test method of a test class
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::TestClass::test_create_game_success -v 
```