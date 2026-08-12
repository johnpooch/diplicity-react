---
paths:
  - "service/**/views.py"
  - "service/**/urls.py"
  - "service/**/serializers.py"
---

# API design

## Put ordinary CRUD on the resource path

List and create hit the collection; retrieve, update, and delete hit one instance. Do not invent verb segments for ordinary CRUD.

| Action | Method | Path |
| --- | --- | --- |
| List | `GET` | `/api/<resource>/` |
| Create | `POST` | `/api/<resource>/` |
| Retrieve | `GET` | `/api/<resource>/<id>/` |
| Update | `PATCH` / `PUT` | `/api/<resource>/<id>/` |
| Delete | `DELETE` | `/api/<resource>/<id>/` |

Nested resources follow the same pattern under their parent.

**Good:**

- Create a member: `POST /api/game/<game_id>/member/`
- Delete a member: `DELETE /api/game/<game_id>/member/<id>/`

**Bad:**

- Create a member via a verb path: `POST /api/game/<game_id>/create-member/`

## Non-CRUD operations use an explicit subpath (`…/join/`, `…/leave/`)

Extra path segments imply an operation beyond ordinary CRUD.

**Example:**

- Join a game: `POST /api/game/<game_id>/member/join`
