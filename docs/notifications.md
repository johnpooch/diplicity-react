# Notifications

How every notification in Diplicity is triggered, addressed, rendered and delivered — and where the
system can currently produce wrong or misleading output.

Every file/line reference below was read from the tree at the time of writing.

---

## 1. Architecture

There is exactly one entry point. Domain code calls `emit(event_type, **kwargs)`
(`service/emit/dispatch.py:6-12`) and three independent consumers react to the same event:

| Consumer | Produces | Registry |
| --- | --- | --- |
| `Notification.objects.create_from_event` | push + email notifications | `service/notification/registry.py` |
| `ChannelEvent.objects.create_from_event` | in-game timeline entries in public press | `service/channel/registry.py` |
| `AgentTask.objects.create_from_event` | bot work items | `service/agent/registry.py` |

All three registries are imported at app-ready time so the `@register` decorators run
(`service/emit/apps.py`).

This document covers the first consumer. The second is mentioned where it overlaps, because a player
who sees a timeline entry but no push (or vice versa) is looking at these two registries disagreeing.

### The pipeline

```
domain code
  └─ emit(event_type, game=…, phase=…, actor=…, recipients=[…], **payload)
       └─ build_context(...)                     → EmitContext        emit/context.py:17-30
            └─ get_spec(event_type, context)     → NotificationSpec   notification/registry.py:19-23
                 ├─ spec.get_recipients()        → set[user_id]       notification/registry.py:38-44
                 ├─ Notification rows (1/recipient)                   notification/models.py:20-22
                 ├─ spec.render(channel) per channel                  notification/registry.py:64-85
                 ├─ NotificationDelivery rows (1/recipient/channel)   notification/models.py:40-56
                 └─ deliver.defer(delivery_ids=[…])                   notification/models.py:58-60
                      └─ procrastinate worker
                           ├─ _send_push  → FCM   notification/tasks.py:41-50
                           └─ _send_email → Resend notification/tasks.py:53-56
```

### Context building

`build_context` (`service/emit/context.py:17-30`) normalises three shorthand forms:

- `message=…` → derives `game`, `phase` (`message.phase` or the game's last phase), `actor`,
  `channel`, and puts the message text in `payload["body"]`.
- `draw_proposal=…` → derives `game`, `phase`, `actor`.
- `phase=…` with no `game` → derives `game` from the phase.

Everything else passed as `**kwargs` lands in `payload`. `recipients=[…]` is just a payload key that
the default audience resolver happens to read.

### Spec resolution and audience

`NotificationSpec` (`service/notification/registry.py:26-99`) is the base class. The knobs are:

| Attribute / method | Default | Meaning |
| --- | --- | --- |
| `channels` | `[PUSH]` | which transports render a delivery row |
| `exclude_actor` | `False` | drop the acting user from the audience |
| `get_audience()` | `payload["recipients"]` | the raw recipient list |
| `get_title()` | `game.name` | push title |
| `get_body()` | — | push body (required) |
| `get_link()` | `{FRONTEND_URL}/game/{game.id}` | deep link |
| `get_email_subject()` | `game.name` | email subject |
| `get_email_body()` | `get_body()` | email body, wrapped by `notification_email` |
| `email_link_text` | `"View Game"` | CTA label in the email |

`get_recipients()` drops `None` ids and, when `exclude_actor` is set, the actor
(`service/notification/registry.py:38-44`). If the resulting set is empty, nothing is created and no
job is deferred (`service/notification/models.py:17-19`).

Audience helpers live on `Game` (`service/game/models.py:680-694`):

- `member_user_ids(include_gm=…)` — every member, including eliminated / kicked / civil-disorder.
- `active_member_user_ids(include_gm=…)` — excludes `eliminated`, `kicked` **and `civil_disorder`**.
- `winner_user_ids()` / `winner_members()` — from the `Victory` row.

### Rendering

`render(channel)` (`service/notification/registry.py:64-85`) produces the row content once per
channel and that same content is reused for every recipient in the broadcast. Push rows carry
`data = {"game_id": …, "link": …}`; email rows carry the full HTML from
`email_service.templates.notification_email` and a `null` link.

When the spec has no game in context (only `game_deleted` today), `link` and `data` are both `None`
(`service/notification/registry.py:65`, `87-89`), so the push is not tappable.

### Persistence

- `Notification` — one row per recipient per event; `recipient` is `SET_NULL`
  (`service/notification/models.py:27-36`).
- `NotificationDelivery` — one row per recipient per channel, with `channel`, `heading`, `body`,
  `link`, `data`, `status` (`pending`/`sent`/`failed`) and `error`
  (`service/notification/models.py:71-93`).

Email rows are only created for recipients with `profile.email_notifications_enabled=True`
(`service/notification/models.py:46-52`, `63-68`).

Rows older than 30 days are deleted nightly at 03:00 UTC by `notification.prune`
(`service/notification/tasks.py:59-63`), cascading to deliveries.

### Delivery

`notification.deliver` (`service/notification/tasks.py:16-38`) loads the batch, splits it by channel,
and calls one transport per channel group. Each group is marked `sent` or `failed` as a unit.

- **Push** — `send_notification_to_users` (`service/notification/utils.py:7-33`) builds a single FCM
  `Message` with a `notification` block (title/body) plus `data` (including `type` = the event type)
  and sends it to every active `FCMDevice` of every recipient in one call. No-ops silently when
  `settings.FIREBASE_APP` is unset or the recipients have no active devices.
- **Email** — `send_email_to_users` (`service/email_service/utils.py:28-39`) re-filters recipients on
  `email_notifications_enabled` and sends one Resend email per address.

Both transports are `emit`ted **inside** the caller's transaction rather than via
`transaction.on_commit`, e.g. `service/member/views.py:60-63`, `service/phase/models.py:612-640`.
Procrastinate's Django integration writes the job row on the same connection, so a rollback discards
the job too — but this does mean the delivery job is invisible until the (sometimes long)
adjudication transaction commits.

---

## 2. The client side

### Registering a device

Token acquisition is platform-split in `packages/web/src/utils/notificationToken.ts:13-39`:

| Platform | Path | Device `type` |
| --- | --- | --- |
| iOS / Android (Capacitor) | `@capacitor-firebase/messaging` (`src/messaging-native.ts`) | `ios` / `android` |
| Web | Firebase JS SDK + `/firebase-messaging-sw.js` service worker (`src/messaging.ts`) | `web` |

Three code paths create the device record, all `POST /devices/`:

1. `useCheckNotificationPermission` (`src/hooks/useCheckNotificationPermission.ts:16-35`) — the
   explicit prompt. Only prompts when permission is still `prompt`/`default`; toasts a warning if
   already denied.
2. `useNotificationPermissionPrompt` (`src/hooks/useNotificationPermissionPrompt.ts:43-80`) — fires
   the prompt once per session as soon as the user has an active non-sandbox game, and silently
   re-registers if permission is granted but no active device row exists for this platform.
3. `useMessaging` (`src/hooks/useMessaging.ts:70-87`, `105-141`) — the settings toggle, plus a native
   `tokenReceived` listener that re-registers on FCM token rotation.

Server-side, `NotificationDeviceViewSet` (`service/notification/views.py:5-28`) deactivates the
user's other active devices **of the same type** on every create/update. Combined with fcm-django's
`UPDATE_ON_DUPLICATE_REG_ID` default of `True`, re-registering a token that already belongs to
another user reassigns it, so a shared handset does not leak another player's notifications.

**Consequence:** a user can only have one active device per type. Two Android phones means only the
most recently registered one receives pushes. `deactivate_stale_devices`
(`service/notification/management/commands/deactivate_stale_devices.py`) enforces the same invariant
in bulk, keeping the highest-id active device per `(user, type)`.

### Receiving

| Situation | Handler |
| --- | --- |
| Native, app foregrounded | `notificationReceived` → `queryClient.invalidateQueries()` (`src/hooks/useMessaging.ts:90-103`) |
| Web, tab foregrounded | `onMessage` → `queryClient.invalidateQueries()` (same) |
| Native, tapped | `notificationActionPerformed` → reads `data.link` (`src/messaging-native.ts:41-53`) |
| Web, tapped | service worker `notificationclick` → reads `data.FCM_MSG.data.link`, focuses an open tab and `postMessage`s it, else `openWindow` (`public/firebase-messaging-sw.js:21-38`) |

Both tap paths funnel into `parseDeepLinkUrl` → `deepLinkStorage.setPendingPath`
(`packages/web/src/App.tsx:97-111`), which the router consumes after auth.

Background display on native is handled by FCM itself, because every message carries a `notification`
block (`service/notification/utils.py:24-27`) — the app is not involved.

---

## 3. Catalogue

21 event types have notification specs. `service/notification/tests.py:182-206` pins the exact set.

"All members" = `member_user_ids(include_gm=True)` — includes eliminated, kicked and
civil-disorder players. "Active members" = `active_member_user_ids(include_gm=True)` — excludes all
three.

| Event | Trigger | Audience | Channels | Timeline entry |
| --- | --- | --- | --- | --- |
| `channel_message` | `channel/serializers.py:42` — message created | channel members, minus sender | push | no |
| `draw_proposal` | `draw_proposal/models.py:61` — proposal created | active members, minus proposer | push | no |
| `game_start` | `game/models.py:758` — `Game.start()` | all members | push + email | yes |
| `game_draw` | `game/models.py:779` — `emit_game_ended()` | all members | push | yes |
| `game_solo_win` | `game/models.py:781` | winners only | push | yes |
| `game_solo_loss` | `game/models.py:782` | all members, minus winners | push | yes |
| `phase_resolved` | `phase/models.py:645-652`, called from `:904` | all members | push + email | yes |
| `phase_resolved_early` | same site, fixed-time game resolving before deadline | all members | push + email | yes |
| `game_deleted` | `game/views.py:158` — GM deletes | explicit list, minus deleter | push | no |
| `game_admin_reassigned` | `game/models.py:660` — `reassign_admin()` | the new admin only | push | yes |
| `game_paused` | `game/serializers.py:662` | all members, minus actor | push | yes |
| `game_resumed` | `game/serializers.py:678` | all members, minus actor | push | yes |
| `game_deadline_extended` | `game/serializers.py:703` | all members, minus actor | push | yes |
| `kicked_from_staging` | `member/views.py:63` — GM kicks from a pending game | the kicked user | push | no |
| `removed_from_staging` | `phase/models.py:551` — CD auto-removal | the removed user | push | no |
| `civil_disorder` | `phase/models.py:526` — after adjudication | **active** members | push + email | yes |
| `civil_disorder_recovery` | `member/views.py:90` | active members, minus returning player | push | yes |
| `elimination` | `phase/models.py:590` | the eliminated player | push | yes |
| `nmr_extension_used` | `phase/models.py:287` | the player who burned the extension | push | no |
| `nmr_extension_applied` | `phase/models.py:289` | all members | push | yes |
| `deadline_warning` | `phase/models.py:389` — minutely sweep | one player at a time | push + email | no |

Two events flow through `emit` but have **no** notification spec, by design: `phase_started`
(drives bot tasks, `service/agent/registry.py`) and `phase_state_confirmed`.

### Copy and links, by event

All bodies are in `service/notification/registry.py`. The title is the game name unless stated.

**`channel_message`** (`:102-123`) — `"{sender}: {body}"`, body truncated to 3 lines / 200 chars.
Sender renders as `"Anonymous"` while `game.anonymity_active`, or `"Deleted User"` if the account is
gone (`:95-99`). Links straight to the channel:
`/game/{id}/phase/{phase_id}/chat/channel/{channel_id}`.

**`draw_proposal`** (`:126-137`) — `"{proposer} has proposed a draw. Respond to it now."` Links to
`/game/{id}/phase/{phase_id}/draw-proposals`.

**`game_start`** (`:140-151`) — `"The game has started…"`. Email subject `"{game} — Game Started"`.

**`game_draw`** (`:154-161`) — names the winners via `Victory.members`. Safe to use real names here
because `anonymity_active` is false once the game is `COMPLETED` (`service/game/models.py:542-544`).

**`game_solo_win`** / **`game_solo_loss`** (`:164-181`) — congratulation vs. `"{winner} achieved a
solo win"`. Emitted as two separate events from the same call site.

**`phase_resolved`** / **`phase_resolved_early`** (`:184-209`) — `"{phase.name} has been resolved"` /
`"{phase.name} resolved early — all players confirmed their orders."` `phase.name` is
`"{season} {year}, {type}"` (`service/phase/models.py:950-951`). The "early" variant is chosen when
the game is `FIXED_TIME` and resolution happened before `scheduled_resolution`
(`service/phase/models.py:645-652`).

**`game_deleted`** (`:212-218`) — title is the payload's `game_name` (the game row is already gone).
No link, no `data`.

**`game_admin_reassigned`** (`:221-228`) — sent only to the new admin.

**`game_paused` / `game_resumed` / `game_deadline_extended`** (`:231-263`) — share
`GameManagementSpec`. The actor is described as `"the Game Master"` or `"the game creator"`
(`service/game/models.py:539-540`), with `" ({username})"` appended unless anonymity is active.
Resume and extend append `"New deadline: {formatted_deadline}"`, falling back to the literal string
`"N/A"` when the game has no current phase or no scheduled resolution (`:243-245`).

**`kicked_from_staging`** (`:266-269`) — `"You were removed from this game by {manager_label}."`

**`removed_from_staging`** (`:272-278`) — title `"Removed from staging games"`, body
`"You were removed from {game.name} because you entered civil disorder in an active game."` Note the
game named in the body is the *staging* game the player lost, not the game where CD happened.

**`civil_disorder`** (`:281-298`) — title `"Civil Disorder"`, body
`"{nation_names} entered civil disorder."` Link deliberately `None`.

**`civil_disorder_recovery`** (`:301-317`) — title `"Player Returned"`, body
`"{nation} has returned from civil disorder."` Link `None`.

**`elimination`** (`:320-323`) — sent to the eliminated player only.

**`nmr_extension_used`** (`:326-337`) — `"You did not submit orders and used an automatic extension
({n} remaining). The current phase is extended until {deadline}."`

**`nmr_extension_applied`** (`:340-347`) — the anonymised version for everyone else.

**`deadline_warning`** (`:350-359`) — body is fully precomputed at the call site by
`build_notification_body` (`service/phase/utils.py:29-81`) and passed in the payload. Email subject
`"{game} — Deadline Approaching"`, CTA `"Submit Orders"`.

### How deadline warnings are scheduled

`Phase.objects.send_deadline_warnings()` (`service/phase/models.py:293-401`) runs every minute
(`service/phase/tasks.py:23-27`). Per active, unpaused, non-sandbox phase:

1. Pick a warning threshold from the phase duration (`:294-311`) — 15 min for a 1 h phase, 1 h up to
   24 h, 2 h up to 96 h, 4 h beyond.
2. Skip unless `0 < time_until_deadline <= threshold`.
3. Skip players with `has_possible_orders=False`, players already warned for this
   `scheduled_resolution` (`ps.deadline_warning_sent_for`), and players whose actionable unit count
   is zero (`:375-376`).
4. Build copy from `(orders_confirmed, deadline_mode, orders_given, total_units, time_left,
   extensions_remaining)`. Returns `None` — i.e. no notification — when the player has already
   confirmed (`service/phase/utils.py:42-43`, `61-62`).

The dedupe key is the deadline itself, so any deadline change (GM extension, NMR extension) re-arms
the warning for that phase.

---

## 4. Known and suspected problems

The Discord reports are: warnings that claim you have no orders in when you do, "you used an
extension" when you didn't, "removed for civil disorder" when neither happened, and phase-resolved
pushes for phases that already resolved long ago. Here is what the code supports.

### 4.1 Confirming with zero orders is recorded as an NMR — confirmed bug

`_set_orders_outcome` (`service/phase/models.py:403-418`) classifies a phase state as `NMR` purely on
`Count("orders") == 0`. It never looks at `orders_confirmed`. `_check_and_apply_nmr_extensions`
(`:254-259`) uses the same rule.

Submitting no orders is a legal move (everything holds), and nothing stops a player confirming an
empty order set — the serializer just toggles the flag (`service/phase/serializers.py:33-45`) and the
UI's Confirm button is only disabled while the request is in flight
(`packages/web/src/screens/GameDetail/OrdersScreen.tsx:306-312`).

So a player who deliberately confirms zero orders:

1. Gets `nmr_extension_used` — "You did not submit orders and used an automatic extension" — and
   loses an extension (`:276-287`). **This is the "told you've used an extension when you haven't"
   report.**
2. Has the phase deadline pushed out for the whole game, and everyone gets `nmr_extension_applied`
   (`:269-289`) — even though every player confirmed.
3. Is recorded `NMR` for civil-disorder purposes. Two such movement phases in a row → civil disorder
   (`:420-471`) → removal from every pending game they had joined (`:528-555`) →
   `removed_from_staging`. **This is the "removed because I entered civil disorder, despite neither
   happening" report.**

Fix direction: treat `orders_confirmed=True` as "orders received" in both `_set_orders_outcome` and
`_check_and_apply_nmr_extensions`.

### 4.2 The player who enters civil disorder is never told — confirmed gap

`CivilDisorderSpec.get_audience()` is `active_member_user_ids(include_gm=True)`
(`service/notification/registry.py:285-286`), which excludes members with `civil_disorder=True`
(`service/game/models.py:684-687`). The flag is set before the emit
(`service/phase/models.py:464-466` then `:526`), so the players who just entered civil disorder are
filtered out of their own notification.

Their first and only signal is `removed_from_staging`, which names a *different* game than the one
where they NMR'd. That is precisely how the Discord report reads: a removal notice from a game they
were only queuing for, citing a civil disorder they were never told about.

### 4.3 `has_possible_orders` is not the same as "has something to do" — likely bug

`send_deadline_warnings` explicitly guards against zero actionable units before warning
(`service/phase/models.py:355-376`), which is only necessary because `has_possible_orders` can be
`True` for a nation with nothing to order — e.g. an adjustment phase where supply centres equal
units.

`_check_and_apply_nmr_extensions` has no equivalent guard (`service/phase/models.py:254-264`). Any
player in that state is treated as having NMR'd, burns an extension, and delays the phase for
everyone. This compounds 4.1.

### 4.4 Warning copy goes stale the moment the deadline moves — confirmed

`deadline_warning` bodies bake `time_left` at render time (`service/phase/models.py:378-389`), and
the notification is then queued for asynchronous delivery.

The deadline moves immediately afterwards in two ordinary situations:

- an NMR extension at the moment the deadline passes (`service/phase/models.py:273-274`);
- a GM extending the deadline (`service/game/serializers.py:700-703`).

Both happen *after* warnings for that deadline were already rendered and enqueued. The player then
reads "1 hour remaining" while the app shows a day. **This matches the "told you have one hour left
even though there's lots of time left" report.** Any queue backlog widens the same window.

Fix direction: render the deadline as an absolute timestamp rather than a relative duration, or
re-check freshness in `deliver` before sending.

### 4.5 Delivery status is meaningless — confirmed

`_deliver_channel` marks a whole channel group `sent` unless the transport raises
(`service/notification/tasks.py:27-38`). Neither transport raises:

- `send_notification_to_users` catches every FCM exception itself
  (`service/notification/utils.py:29-33`) and returns silently when Firebase is unconfigured or the
  recipients have no active devices (`:11-19`).
- `send_email` catches every Resend exception per address (`service/email_service/utils.py:14-25`).

So `NotificationDelivery.status` is effectively always `sent` and `error` is always null, including
when nothing was sent at all. **The delivery table cannot currently answer "did this player actually
receive it?"** — which is the first question any of these reports needs answered.

Fix direction: let the transports raise, or return a per-recipient result that `_deliver_channel`
records.

### 4.6 `deliver` is not idempotent — confirmed, plausible cause of stale duplicates

`deliver` is registered with `retry=3` (`service/notification/tasks.py:16`) and re-reads its batch by
id with no `status` filter (`:18-24`). Any retry — worker restart, connection blip, a failure between
`send` and the status update — re-sends every push in the batch, including ones already delivered.

Because procrastinate retries with backoff and the copy is baked at enqueue time, a retried
`phase_resolved` arrives describing a phase that resolved much earlier. **This is the most plausible
mechanism behind "told that Fall 1905 adjudicated when it's currently Fall 1906".** There is no
freshness check anywhere in the delivery path.

Fix direction: filter on `status=PENDING` when loading the batch, and skip deliveries older than some
sanity window.

### 4.7 One push per batch, addressed to everyone — by design, worth knowing

`_send_push` takes `heading`, `body` and `data` from `deliveries[0]` and applies them to every
recipient in the batch (`service/notification/tasks.py:41-50`). This is safe today because
`broadcast` renders content once per channel and reuses it for all recipients
(`service/notification/models.py:41-53`) — but it means a spec can never personalise per recipient
within a single emit. `nmr_extension_used` works around this by emitting once per member
(`service/phase/models.py:284-287`).

### 4.8 Smaller issues

- **Dead links.** `removed_from_staging` links to the staging game (`registry.py:52-56`), which
  `delete_if_empty_pending()` may delete moments later (`service/phase/models.py:553-555`).
- **Untappable pushes.** `civil_disorder`, `civil_disorder_recovery` (`registry.py:288-289`,
  `308-309`) and `game_deleted` (`registry.py:65`) carry no `link`, so the tap handlers no-op
  (`public/firebase-messaging-sw.js:23-24`).
- **`"N/A"` deadlines.** `game_resumed` and `game_deadline_extended` fall back to the literal string
  `"New deadline: N/A"` when there is no current phase or scheduled resolution
  (`registry.py:243-245`).
- **Dormant task.** `email_service.send_email_notification` (`service/email_service/tasks.py:10-16`)
  has no callers — the email path goes through `notification.deliver`. It should be removed per the
  "absent beats dormant scaffolding" rule in `CLAUDE.md`.
- **Leftover helper.** `Game.notification_user_ids` (`service/game/models.py:662-669`) survives for
  exactly one caller, `GameDeleteView` (`service/game/views.py:154`), and duplicates
  `member_user_ids(include_gm=True)` plus an actor exclusion that the registry already models via
  `exclude_actor`.
- **Multi-device users.** Only the most recently registered device per platform stays active
  (`service/notification/views.py:14-28`), so a player with two phones of the same OS only gets
  pushes on one.

---

## 5. Investigating a report

The registry refactor means every notification a player was *supposed* to get is a row. Given a
username:

```sql
SELECT n.created_at, n.event_type, d.channel, d.status, d.heading, d.body, d.error
FROM notification_notification n
JOIN notification_notificationdelivery d ON d.notification_id = n.id
JOIN auth_user u ON u.id = n.recipient_id
WHERE u.username = :username
ORDER BY n.created_at DESC
LIMIT 100;
```

Rows only survive 30 days (`service/notification/tasks.py:59-63`). Read `status` with 4.5 in mind: it
tells you a delivery job ran, not that a push arrived.

To check whether they could have received anything at all:

```sql
SELECT id, type, active, date_created FROM fcm_django_fcmdevice WHERE user_id = :user_id;
```

For "why did this fire", the trigger site in the catalogue table is the place to start; for "why did
it say that", the spec's `get_body` in `service/notification/registry.py`.

---

## 6. Test coverage

- `service/notification/tests.py` — 54 tests: truncation, registry completeness, every audience
  resolver, per-event content for draw proposals and game endings, early-vs-normal phase resolution,
  broadcast row creation, batching, and prune.
- `service/emit/tests.py` — 6 tests: end-to-end dispatch through all three consumers.
- `service/notification/tests_devices.py` — 8 tests: device registration and deactivation.

Not covered today, and directly relevant to section 4:

- `deliver` retry behaviour on an already-`sent` batch (4.6).
- Transport failures reaching `NotificationDelivery.status` (4.5).
- `_set_orders_outcome` / `_check_and_apply_nmr_extensions` for a phase state with
  `orders_confirmed=True` and zero orders (4.1).
- Deadline-warning copy after the deadline moves (4.4).
