---
paths:
  - "service/notification/registry.py"
---

# Notification copy

Every notification a player receives is rendered by a spec in `service/notification/registry.py`. Read that file for the specs themselves; this file states the rules a new one must follow.

A player is usually in several games at once, and reads these on a lock screen, in a notification tray, or in an inbox next to unrelated mail. Reading well in isolation is not the bar — the copy has to be identifiable and actionable in that pile. The base `NotificationSpec` already implements most of what follows, so a spec that overrides only `get_audience` and `get_body` is usually the correct spec.

## Title

**The title is the game name.** Do not override `get_title()` to name the event. A title reading "Civil Disorder" tells a player in five games nothing about which game it came from; the game name tells them, and the body says what happened. The only legitimate override recovers the game name from the payload when the game row is gone by the time the notification renders.

**An event that needs naming goes in the body's first clause**, not the title.

**Title Case for titles, sentence case for bodies.** This applies to `email_link_text` and `get_email_subject()` too, which are titles.

**A spec declaring `Channel.EMAIL` defines `get_email_subject()`**: the game name, an em dash, and the event in Title Case. The bare game name that the base class returns is enough for a push heading sitting under an app icon, but not for an inbox.

## Body

**Present perfect for events that just happened** — "has been resolved", not "resolved" or "will resolve". A notification arrives at the moment of the event; the tense should say so.

**Second person only when the event is about the recipient.** Where one spec tells a player about themselves and its anonymised twin tells everyone else about an unnamed player, the twin stays third person throughout — it must not address the group as "you" for something one of them did.

**Describe what happened, not what the player failed to do.** State the consequence and the new state. The player does not need to be told they were late.

**Calls to action are a field, never prose.** The body states the event; the tap target is `get_link()` and the email button is `email_link_text`. An inline "Respond to it now" duplicates a control the player already has, and reads as nagging in a tray.

**The body must stand alone.** `get_email_body()` defaults to `get_body()`, and `notification_email` (`service/email_service/templates.py`) interpolates that string twice — once into the hidden preview div, once into the visible paragraph. Whatever the body says is what a player sees in a mail list before opening anything.

**No placeholder strings in user-facing copy.** A literal `"N/A"`, an `"Unknown"`, or the empty string left by a lookup that found nothing is a bug that shipped as text. Where the data may be missing, build the clause conditionally and omit it — a shorter sentence always beats a filled-in blank.

## Naming people

**One actor-rendering helper, with one anonymity check.** Every place a spec puts a person into copy goes through it, whether the name comes from `context.actor`, from a member's nation, or from the payload. A spec that formats a name itself will be the one that leaks a name in an anonymous game, because the check on `Game.anonymity_active` lives in the helper and nowhere else.

## Links

**Every push has somewhere to land.** `get_link()` returns the most specific view relevant to the event, not the game root, when one exists. Both tap handlers no-op without a link — the `notificationclick` handler in `packages/web/public/firebase-messaging-sw.js` and the message listener in `packages/web/src/messaging-native.ts` — so a linkless push is a notification that does nothing when tapped.

**`link = None` is a documented exception, not a per-spec judgement call.** A spec may omit the link only where there is genuinely nowhere to send the player, and it records that reason declaratively, so the set of untappable notifications can be read off the registry. An override that returns `None` with no stated reason is not an exception, it is an oversight.
