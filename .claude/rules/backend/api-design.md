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

## Never delete a path that shipped

The iOS and Android apps are Capacitor builds with `webDir: "dist"` — each store release bakes in its own copy of the web bundle and calls whatever paths that bundle was generated against. Deleting a route does not migrate those installs, it breaks them until every user updates. This is what took game joining down for app users in August 2026: `/game/<id>/join/` moved to `/game/<id>/member/join/`, and every shipped build kept POSTing to a path that now 404s.

Renaming a path is fine; removing the old one is not. Leave the old path serving the same view through a subclass excluded from the schema, so codegen keeps emitting only the new path and no client is generated against the alias:

```python
@extend_schema(exclude=True)
class LegacyMemberJoinView(MemberJoinView):
    """Serves POST /game/<id>/join/ for mobile builds shipped before ..."""
```

Register it in the owning app's `urls.py` with a `-legacy` suffix on the URL name, and cover it with a test asserting the literal path — that string is the contract, so `reverse()` alone does not protect it. Aliases are removed once the store metrics show the old builds are gone, not as part of the rename.
