# Django app architecture

## Summary

The Django apps in `service/` have no shared shape for writes. Business rules, locking, transactions, notifications and response building are spread across views, serializers, model managers and permission classes, and each app arranges them differently. This makes a change hard to review, because the reader has to find every place a rule might live, and it makes it hard for an agent to write new code that matches existing code.

This document proposes one structure for every app. Writes go through **commands**: manager methods wrapped in a `@command` decorator that owns the transaction, row locks and the policy check. Rules are small **check** classes grouped into **policies**. Reads go through **loaders**, which own the queryset and batch work behind each output serializer. Views only declare which command or loader they use. A small set of shared classes in `service/common/` supports this, and the first app to adopt it is `draw_proposal`.

## Context

The structure was worked out on a throwaway example app, a lending library with authors, books, loans and holds. The library was chosen because it needs every behaviour the real apps need: actor-dependent rules, rules that depend on related rows, commands that call other commands, scheduled jobs that may fire after the state has moved on, per-actor read data, aggregate counts and filters. The example code in this document is that app in its final form.

Several earlier designs were tried and dropped. A step-list design, where a command was a list of step objects passing values through a shared context dictionary, made the data flow depend on string keys and was hard to read. Policy mixins on models were replaced by standalone policy classes. A `@step` decorator for model write methods was removed because plain model methods were enough. Splitting `@command` into separate lock, policy and transaction decorators was considered and rejected in favour of one decorator, because the three are always applied together and their order matters.

Two external reviews of the example app informed the final naming and file layout. The research behind it compared Ecto.Multi, light-service, dry-operation, django-rules, django-fsm-2 and django-readers. It kept two ideas from them: predicates should be small named objects, and the operation body should be ordinary code rather than a pipeline definition.

## Proposed direction

An app has these parts. Each part is described in its own section below with its rules, the shared class it builds on, and the library example.

1. Models hold fields, read-only properties, and write methods that change one instance or create its direct children.
2. QuerySets hold named filters, and every QuerySet defines `visible_to(actor)`.
3. Managers hold commands, which are the only entry points for writes.
4. Checks are single predicates with a reason code, and policies are ordered lists of checks.
5. Timers declare scheduled jobs for a model, and tasks are one-line procrastinate tasks that call a command.
6. Loaders and hydrators build everything an output serializer reads.
7. Filters map query parameters to QuerySet methods.
8. Serializers validate input shape or describe output, and nothing else.
9. Views declare a loader or call one command.

A write request flows like this. The view validates the request body with an input serializer and calls one command with the target, the actor and the validated values. The command locks the rows it needs, checks its policy against the locked rows, runs model write methods, syncs timers, emits events and calls any follow-on commands, all in one transaction. The view then loads the result through the output serializer's loader and returns it.

A read request flows like this. The view asks the loader for a queryset scoped to the actor, filters and paginates it, lets the loader hydrate the page, and serialises it.

### Where a rule goes

Most placement questions come down to what the rule depends on.

A DRF permission class answers a question about the user alone, such as whether they are signed in or are staff. It never loads a row. In practice a converted view's `permission_classes` is usually just `IsAuthenticated`.

Every other rule is a check, listed in the command's policy. That covers the state of the target row and its related rows, and how the actor relates to them. It also covers rows reached through the URL rather than the target: that the game is active, that it is not a sandbox, that its current phase is active, or that the user is an active player in it. A game found from the URL is still a row.

There are three reasons for drawing the line here:

1. A check runs under the command's row lock, after the state can no longer change underneath it. A permission class runs before the command, against an unlocked read. For example, the current draw proposal code checks that the phase is active as a permission and then checks it again under a lock, because the phase can start resolving between the two.
2. A check can be reported to clients through `Actions` as a `blocked_reason`, so a client does not re-implement game rules to decide whether to show a button. A permission class cannot.
3. "About the user alone, or about a row" leaves fewer judgement calls than "about the request".

Rules shared across many commands, such as being an active player in an active game, become a shared policy that each command's policy includes, the same way `CanRenewPolicy` includes `RenewablePolicy`. Their checks read the game through `game_of(instance)`, which is the instance itself when the target is a game and `instance.game` otherwise, so one check works for the game or any target that has a `game` foreign key. A command that relies on game or phase state locks that row with `locks=`, or targets it.

Finding the game from the URL stays a view concern. A game that does not exist is a 404, not a refusal.

`visible_to` on the QuerySet says which rows an actor may know exist. Reads always apply it, through the loader. A write applies it only where the row's existence must stay hidden from the actor: there the view's `get_queryset` scopes the lookup with `scoped`, and a row the actor cannot see answers 404. Everywhere else a write looks its target up without scoping, and an actor who may not act on the row gets the policy's 403. In particular, do not scope a write lookup when the policy already checks what `visible_to` filters on.

Validating the shape of input (types, choices, lengths, that a referenced row exists) belongs to the input serializer. Whether the input is allowed given the current state is a check.

What happens as a consequence of a write (notifications, follow-on commands, rescheduling jobs) is written in the command body, in order.

## Shared classes

The shared classes live in `service/common/`, next to the existing `BaseModel`, permissions and mixins. `service/common/views.py` and `service/common/serializers.py` already exist, and the new classes are added to them. The other modules are new.

Only add a shared class when an app needs it. The first conversion, `draw_proposal`, needs actors, checks, policies, commands, loaders, the refusal mixin, `LoaderMixin`, `LoaderListView`, `ActionSchema`, `ActionView` and `CreateActionView`. It does not need timers, hydrators, `Actions`, `QuerySetFilter` or `LoaderDetailView`, so those wait for the app that does.

The code below is the shared code in full. It differs from the throwaway example app in these ways, each of which came out of the `draw_proposal` work:

1. `lock_rows` now locks the related rows before the target. This keeps a consistent parent-before-child lock order.
2. `lock_rows` accepts a target instance of a model other than the manager's own.
3. `lock_rows` accepts a property path, such as `current_phase`, which it locks without re-attaching.
4. The conversion of `Refused` into an HTTP error has moved into a `RefusalMixin`.
5. `ActionView` serves `POST`, `PUT`, `PATCH` and `DELETE`, limited per view by `http_method_names`, and does not scope its lookup with `visible_to`.
6. `CreateActionView` extends `CreateAPIView`, so the schema publishes its 201.
7. `LoaderListView` has no filter backend of its own. A list view with a FilterSet declares `filter_backends` beside `filterset_class`.

### Actors

```python
class SystemActor:
    pk = None
    is_authenticated = True
    is_staff = False


SYSTEM = SystemActor()


def scoped(queryset, actor):
    if actor is SYSTEM:
        return queryset
    return queryset.visible_to(actor)
```

The actor is the user performing an operation: `request.user` in a view, and `SYSTEM` when the system performs it, such as in a task or a command called by another command. `SYSTEM` looks like an authenticated non-staff user with no primary key, so checks written against users behave predictably for it. `scoped` is how loaders and views apply `visible_to`, and it lets `SYSTEM` see every row.

The actor is always a user, even in game-scoped apps where the rules are about a `Member`. Checks and commands that need the acting member find it from the actor, the same way `CurrentGameMemberMixin` does. One actor type keeps `visible_to`, `Actions` and `SYSTEM` uniform across apps.

### Checks and decisions

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None = None

    def __bool__(self):
        return self.allowed


ALLOWED = Decision(True)


class Check:
    reason = None

    @classmethod
    def decide(cls, instance, actor):
        if cls().check(instance, actor):
            return ALLOWED
        return Decision(False, cls.reason)

    @classmethod
    def reasons(cls):
        return {cls.reason} - {None}

    def check(self, instance, actor):
        raise NotImplementedError


class SignedInCheck(Check):
    reason = "signed_out"

    def check(self, instance, actor):
        return actor.is_authenticated


class IsStaffCheck(Check):
    reason = "not_staff"

    def check(self, instance, actor):
        return actor.is_staff
```

A `Decision` is falsy when denied, so callers write `if not decision`. Checks are used through the class (`IsOpenCheck.decide(loan, actor)`), which instantiates them, so a policy can list classes rather than instances. `SignedInCheck` and `IsStaffCheck` are the only generic checks. They are not needed by `draw_proposal`, so they are added with the first app that uses them.

### Policies

```python
from .checks import ALLOWED


class Refused(Exception):
    def __init__(self, decision):
        super().__init__(decision.reason)
        self.decision = decision


class Policy:
    checks = ()

    @classmethod
    def decide(cls, instance, actor):
        for check in cls.checks:
            decision = check.decide(instance, actor)
            if not decision:
                return decision
        return ALLOWED

    @classmethod
    def reasons(cls):
        return set().union(*(check.reasons() for check in cls.checks))
```

A policy has the same `decide` and `reasons` interface as a check, which is why a policy can list another policy among its checks. The first failing check decides, so checks are ordered from the most general reason to the most specific.

### Commands

```python
import inspect
from functools import reduce, wraps

from django.db import models, transaction

from .actors import SYSTEM
from .policies import Refused


def select_for_update(instance):
    return type(instance)._default_manager.select_for_update().get(pk=instance.pk)


def lock_rows(model, value, paths):
    target = value if isinstance(value, models.Model) else model._default_manager.get(pk=value)
    related = {}
    for path in paths:
        row = reduce(getattr, path.split("."), target)
        if row is not None:
            related[path] = select_for_update(row)
    target = select_for_update(target)
    for path, row in related.items():
        *parents, attribute = path.split(".")
        parent = reduce(getattr, parents, target)
        if not isinstance(getattr(type(parent), attribute, None), property):
            setattr(parent, attribute, row)
    return target


def command(requires=None, only_if=None, locks=()):
    def decorate(method):
        signature = inspect.signature(method)
        first = list(signature.parameters)[1]
        target_name = None if first == "actor" else first

        @wraps(method)
        def run(manager, *args, **kwargs):
            arguments = signature.bind(manager, *args, **kwargs)
            actor = arguments.arguments.get("actor", SYSTEM)
            with transaction.atomic():
                instance = None
                if target_name is not None:
                    instance = lock_rows(manager.model, arguments.arguments[target_name], locks)
                    arguments.arguments[target_name] = instance
                if only_if is not None and not only_if.decide(instance, actor):
                    return None
                if requires is not None:
                    decision = requires.decide(instance, actor)
                    if not decision:
                        raise Refused(decision)
                return method(*arguments.args, **arguments.kwargs)

        run.policy = requires
        return run

    return decorate
```

The decorator reads the method's signature. The first parameter after `self` is the target, unless it is named `actor`, in which case the command creates something and has no target. The actor is the argument named `actor`, or `SYSTEM` when the command has no such parameter.

Inside one transaction the decorator does four things in order:

1. It re-fetches the target with `SELECT ... FOR UPDATE`. The target may be passed as an instance or a primary key, which is how tasks pass it.
2. It returns `None` without doing anything if `only_if` fails.
3. It raises `Refused` if `requires` fails.
4. It runs the body with the locked target.

Checking after locking means two concurrent requests cannot both pass a policy that only one of them should pass.

`locks` names paths from the target, such as `"book"`, `"book.author"` or `"current_phase"`. Those rows are locked before the target. A foreign key path is re-attached to the locked target, so the policy and the body read the locked row. A property path, such as `Game.current_phase`, cannot be assigned, so its row is locked but not re-attached. Reading the property again queries the row, and because the row is locked, that read sees its committed state and nothing else can change it until the transaction ends. A path is resolved before the target is locked, so if a property names a different row by the time the lock is taken (a phase resolves and the next one starts), the command holds the old row's lock and reads the new row. List a parent path before its child.

The target is normally an instance of the manager's model. A command may take an instance of another model as its target when the operation creates a row belonging to it, for example a command on the draw proposal manager that proposes a draw in a phase. Passing that target as a primary key does not work, because a bare key is looked up on the manager's model.

`run.policy` exposes the `requires` policy, so an output serializer can report whether the actor could run the command now.

Nested commands join the outer transaction, and Django uses a savepoint for the inner `atomic` block. Re-locking a row the transaction already holds does not block.

### Timers

```python
from procrastinate.contrib.django import app


class Timer:
    task = None
    job_id_field = None

    def run_at(self, instance):
        raise NotImplementedError

    def sync(self, instance):
        current_job_id = getattr(instance, self.job_id_field)
        if current_job_id is not None:
            app.job_manager.cancel_job_by_id(current_job_id)
        run_at = self.run_at(instance)
        job_id = None
        if run_at is not None:
            job_id = app.configure_task(self.task, schedule_at=run_at).defer(pk=instance.pk)
        type(instance).objects.filter(pk=instance.pk).update(**{self.job_id_field: job_id})
        setattr(instance, self.job_id_field, job_id)


def sync_timers(*instances):
    for instance in instances:
        for timer in instance.timers:
            timer.sync(instance)
```

A timer describes one scheduled job for a model as a function of the model's state. `run_at` returns when the job should run, or `None` when no job should be scheduled. `sync` cancels the existing job and schedules a new one, so a command never reasons about whether a job is already scheduled. It calls `sync_timers` after any write that could change a `run_at` result.

### Hydrators

```python
class Hydrator:
    def hydrate(self, instances, actor):
        raise NotImplementedError


class AggregateHydrator(Hydrator):
    attribute = None
    queryset = None
    key = None
    value = None
    default = None

    def hydrate(self, instances, actor):
        rows = (
            self.queryset.filter(**{f"{self.key}__in": [instance.pk for instance in instances]})
            .order_by()
            .values(self.key)
            .annotate(value=self.value)
            .values_list(self.key, "value")
        )
        values = dict(rows)
        for instance in instances:
            setattr(instance, self.attribute, values.get(instance.pk, self.default))
```

A hydrator sets an attribute on every instance of a page with one query for the whole page. It is used for values that cannot be expressed as `select_related` or `prefetch_related`, such as counts, and values that depend on the actor. `AggregateHydrator` covers grouped aggregates declaratively.

### Loaders

```python
from django.db.models import Prefetch

from .actors import scoped


class Loader:
    queryset = None
    hydrators = ()
    nested = {}

    @classmethod
    def get_queryset(cls, actor):
        return scoped(cls.queryset.all(), actor).prefetch_related(
            *(Prefetch(lookup, queryset=loader.get_queryset(actor)) for lookup, loader in cls.nested.items())
        )

    @classmethod
    def hydrate(cls, instances, actor):
        instances = list(instances)
        for hydrator in cls.hydrators:
            hydrator.hydrate(instances, actor)
        for lookup, loader in cls.nested.items():
            loader.hydrate([child for instance in instances for child in getattr(instance, lookup).all()], actor)
        return instances

    @classmethod
    def get(cls, pk, actor):
        instances = cls.hydrate(cls.get_queryset(actor).filter(pk=pk), actor)
        return instances[0] if instances else None
```

A loader owns everything one output serializer needs: the base queryset with its joins and prefetches, the hydrators, and nested loaders for nested serializers. `nested` maps a prefetch lookup to the loader of the nested serializer, so a nested list is scoped and hydrated the same way as a top-level one. `get` loads a single row, which is how command responses are built.

### Filters

```python
from django_filters import rest_framework as filters


class QuerySetFilter(filters.BooleanFilter):
    def __init__(self, queryset_method, **kwargs):
        self.queryset_method = queryset_method
        super().__init__(**kwargs)

    def filter(self, queryset, value):
        if value is None:
            return queryset
        matching = getattr(queryset, self.queryset_method)()
        return matching if value else queryset.exclude(pk__in=matching.values("pk"))
```

`QuerySetFilter` exposes a QuerySet method as a boolean query parameter, so the meaning of "on shelf" or "open" lives in the QuerySet and nowhere else. `false` returns the complement.

### Serializers

```python
from rest_framework import serializers


class Actions(serializers.ListField):
    def __init__(self, **commands):
        self.policies = {key: command.policy for key, command in commands.items()}
        reasons = sorted(set().union(*(policy.reasons() for policy in self.policies.values())))
        self.action_class = type(
            "Action",
            (serializers.Serializer,),
            {
                "key": serializers.ChoiceField(choices=list(commands)),
                "blocked_reason": serializers.ChoiceField(choices=reasons, allow_null=True),
            },
        )
        super().__init__(child=self.action_class(), source="*", read_only=True)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        self.action_class.__name__ = type(parent).__name__.removesuffix("OutputSerializer") + "Action"

    def to_representation(self, instance):
        actor = self.context["request"].user
        return [
            {"key": key, "blocked_reason": policy.decide(instance, actor).reason}
            for key, policy in self.policies.items()
        ]


class OutputSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields
```

`Actions` lists the commands a client could offer on a row, with a `blocked_reason` for each, taken from the command's own policy. The client never re-implements a rule to decide whether to show a button. The reason codes become an enum in the OpenAPI schema. The `bind` override names the generated component after the parent serializer, such as `BookAction`. Without it, every `Actions` field produces a component called `Action` with different enums, and drf-spectacular reports a collision. This override has not been run against drf-spectacular yet and should be checked when the first app uses `Actions`.

`OutputSerializer` is a `ModelSerializer` whose fields are all read-only, so field types come from the model and an output serializer cannot be used for input by mistake.

### Views

```python
from django.http import Http404
from drf_spectacular.openapi import AutoSchema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .policies import Refused


class RefusalMixin:
    def handle_exception(self, exc):
        if isinstance(exc, Refused):
            exc = PermissionDenied({"code": exc.decision.reason})
        return super().handle_exception(exc)


class LoaderMixin:
    def get_loader(self):
        return self.get_serializer_class().Meta.loader


class LoaderListView(LoaderMixin, generics.ListAPIView):
    def get_queryset(self):
        return self.get_loader().get_queryset(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        instances = self.get_loader().hydrate(queryset if page is None else page, request.user)
        data = self.get_serializer(instances, many=True).data
        return Response(data) if page is None else self.get_paginated_response(data)


class LoaderDetailView(LoaderMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        instance = self.get_loader().get(kwargs[self.lookup_field], request.user)
        if instance is None:
            raise Http404
        return Response(self.get_serializer(instance).data)


class ActionSchema(AutoSchema):
    def get_request_serializer(self):
        return self.view.input_serializer_class


class ActionMixin(RefusalMixin, LoaderMixin):
    schema = ActionSchema()
    input_serializer_class = None
    success_status = status.HTTP_200_OK

    def act(self, *args):
        result = self.perform(*args, **self.get_input())
        instance = self.get_loader().get(result.pk, self.request.user)
        return Response(self.get_serializer(instance).data, status=self.success_status)

    def get_input(self):
        if self.input_serializer_class is None:
            return {}
        serializer = self.input_serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)


class ActionView(ActionMixin, generics.GenericAPIView):
    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        return self.act(self.get_object())

    put = post
    patch = post

    def delete(self, request, *args, **kwargs):
        self.perform(self.get_object(), **self.get_input())
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateActionView(ActionMixin, generics.CreateAPIView):
    success_status = status.HTTP_201_CREATED

    def post(self, request, *args, **kwargs):
        return self.act()
```

`RefusalMixin` turns a `Refused` raised anywhere in the request into a 403 with the reason as its `code`. Every refusal answers 403, whether the rule is about the actor's relationship to a row or the row's state, because both are now checks. A 400 means only that the input serializer rejected the request body.

`ActionView` looks up the target with DRF's generic lookup through the view's queryset. It does not apply `visible_to`; a view whose rows must stay hidden scopes its own `get_queryset`, as described in the placement rules. It validates the body with `input_serializer_class`, passes the validated values to `perform` as keyword arguments, and responds with the result loaded through the output serializer's loader. It serves `POST` by default. A view that serves other methods declares them with `http_method_names`: `PUT` and `PATCH` respond like `POST`, and `DELETE` responds 204 with no body. `ActionSchema` makes the OpenAPI request body the input serializer and the response the output serializer. `CreateActionView` is the same without a target, and responds 201.

## The parts of an app

A converted app has these modules. Modules the app does not need are left out.

```
models.py        fields, properties, write methods
querysets.py     QuerySet classes with visible_to and named filters
managers.py      managers holding @command methods
checks.py        Check classes
policies.py      Policy classes
timers.py        Timer classes
tasks.py         procrastinate tasks, one command call each
hydrators.py     Hydrator classes
loaders.py       Loader classes
filters.py       FilterSets
serializers.py   input and output serializers
views.py         views
urls.py          routes
```

Converted apps are recognised by content: if an app's `managers.py` uses `@command`, new code in that app follows this pattern. In an app that has not been converted, new code follows that app's existing style. Code in an unconverted app is not half-converted.

### Models

A model class has, in order, its manager and timers, its fields and `Meta`, its read-only properties, and its write methods.

Properties describe the row and read related data only through `.all()` on relations, so they use whatever the loader prefetched and do not issue their own filtered queries. For example, `Book.current_loan` iterates `self.loans.all()` rather than calling `self.loans.filter(...)`.

A write method changes that one instance with `save(update_fields=[...])`, or creates a direct child through a reverse relation, such as `self.loans.create(...)`. It does not start a transaction, check permissions, emit events, sync timers or call other models' write methods. Those are the command's job. Write methods are called only from commands.

```python
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .managers import AuthorManager, BookManager, HoldManager, LoanManager
from .timers import DueReminderTimer, DueTimer, HoldExpiryTimer


class Author(BaseModel):
    objects = AuthorManager()

    name = models.CharField(max_length=200)

    def add_book(self, title, reference_only):
        return self.books.create(title=title, reference_only=reference_only)


class Book(BaseModel):
    objects = BookManager()

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    reference_only = models.BooleanField(default=False)
    loan_days = models.PositiveSmallIntegerField(default=14)
    withdrawn_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["title"]

    @property
    def current_loan(self):
        return next((loan for loan in self.loans.all() if loan.is_open), None)

    @property
    def is_on_shelf(self):
        return self.current_loan is None

    @property
    def open_holds(self):
        return sorted((hold for hold in self.holds.all() if hold.is_open), key=lambda hold: hold.created_at)

    @property
    def next_waiting_hold(self):
        return next((hold for hold in self.open_holds if not hold.is_offered), None)

    def open_loan(self, borrower):
        return self.loans.create(borrower=borrower, due_at=timezone.now() + timedelta(days=self.loan_days))

    def place_hold(self, holder):
        return self.holds.create(holder=holder)


class Loan(BaseModel):
    objects = LoanManager()
    timers = (DueReminderTimer(), DueTimer())

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="loans")
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loans")
    due_at = models.DateTimeField()
    renewals = models.PositiveSmallIntegerField(default=0)
    overdue_at = models.DateTimeField(null=True)
    returned_at = models.DateTimeField(null=True)
    reminder_job_id = models.BigIntegerField(null=True, editable=False)
    due_job_id = models.BigIntegerField(null=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_open(self):
        return self.returned_at is None

    @property
    def is_due(self):
        return self.is_open and self.overdue_at is None and self.due_at <= timezone.now()

    def extend(self, days):
        self.due_at += timedelta(days=days)
        self.renewals += 1
        self.save(update_fields=["due_at", "renewals", "updated_at"])

    def mark_overdue(self):
        self.overdue_at = timezone.now()
        self.save(update_fields=["overdue_at", "updated_at"])

    def close(self):
        self.returned_at = timezone.now()
        self.save(update_fields=["returned_at", "updated_at"])


class Hold(BaseModel):
    objects = HoldManager()
    timers = (HoldExpiryTimer(),)

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="holds")
    holder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holds")
    offered_at = models.DateTimeField(null=True)
    closed_at = models.DateTimeField(null=True)
    expiry_job_id = models.BigIntegerField(null=True, editable=False)

    class Meta:
        ordering = ["created_at"]

    @property
    def is_open(self):
        return self.closed_at is None

    @property
    def is_offered(self):
        return self.is_open and self.offered_at is not None

    def offer(self):
        self.offered_at = timezone.now()
        self.save(update_fields=["offered_at", "updated_at"])

    def close(self):
        self.closed_at = timezone.now()
        self.save(update_fields=["closed_at", "updated_at"])
```

### QuerySets

A QuerySet method returns a QuerySet and is named for the rows it describes, such as `open()` or `on_shelf()`, not for the screen that uses it. QuerySets never write.

Every QuerySet defines `visible_to(actor)`, which returns the rows the actor may know exist. When every row is visible to anyone who can reach the endpoint, it returns `self`. It is defined anyway, so that loaders, and views whose rows must stay hidden, can always call it.

Managers are built with `Manager.from_queryset`, so QuerySet methods are available on `Model.objects` without hand-written pass-through methods.

```python
from django.db import models


class AuthorQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self


class BookQuerySet(models.QuerySet):
    def visible_to(self, actor):
        if actor.is_staff:
            return self
        return self.filter(withdrawn_at__isnull=True)

    def on_shelf(self):
        return self.exclude(loans__returned_at__isnull=True)


class LoanQuerySet(models.QuerySet):
    def visible_to(self, actor):
        if actor.is_staff:
            return self
        if not actor.is_authenticated:
            return self.none()
        return self.filter(borrower=actor)

    def open(self):
        return self.filter(returned_at__isnull=True)


class HoldQuerySet(models.QuerySet):
    def visible_to(self, actor):
        if actor.is_staff:
            return self
        if not actor.is_authenticated:
            return self.none()
        return self.filter(holder=actor)

    def open(self):
        return self.filter(closed_at__isnull=True)
```

### Managers and commands

A manager contains only commands. A command is one operation that a user or the system performs on that model, named with a verb (`borrow`, `renew`, `check_in`, `expire`). Its parameters come in this order:

1. the target
2. `actor`, when a person performs it
3. the input values

A creation command starts with `actor`.

A command body is an ordered sequence of model write methods, `sync_timers` calls, `emit` calls and calls to other commands. Read it top to bottom to know everything the operation does. A body may branch when the operation has more than one outcome. It decides the branch with a policy, as `process_due` does with `RenewablePolicy`, or with a property of the locked row, so the rule is still named. When the new row has no parent model in the same app to create it, a creation command may call its own manager's `create`.

A command returns the row the response should show, which is not always the target: `borrow` takes a book and returns the new loan.

Use `requires` for operations a person asks for, where a failure is something the caller needs to hear about. Use `only_if` for operations the system triggers, such as tasks and follow-on commands, where the state may have moved on since the job was scheduled and doing nothing is the correct outcome. A command can have both.

A follow-on command guards itself with `only_if`, and its callers call it without a condition. `check_in` calls `offer_next_hold` whether or not a hold is waiting, and `ReadyToOfferPolicy` decides. Repeating the condition at the call site would put the rule in two places.

A command that needs another app's model imports the app's own `models` module (`from . import models`) and refers to `models.Book.objects`, because the models module imports the managers.

Managers do not grow helper methods. A helper that reads is a property or a QuerySet method. A helper that writes is a model write method. An operation is a command.

```python
from django.db.models import Manager

from emit.dispatch import emit

from . import models
from .checks import IsDueCheck, IsOfferedCheck, IsOpenCheck
from .common.actors import SYSTEM
from .common.commands import command
from .common.timers import sync_timers
from .policies import (
    CanAddBookPolicy,
    CanBorrowPolicy,
    CanCheckInPolicy,
    CanCollectHoldPolicy,
    CanRenewPolicy,
    CanReservePolicy,
    ReadyToOfferPolicy,
    RenewablePolicy,
)
from .querysets import AuthorQuerySet, BookQuerySet, HoldQuerySet, LoanQuerySet


class AuthorManager(Manager.from_queryset(AuthorQuerySet)):
    pass


class BookManager(Manager.from_queryset(BookQuerySet)):
    @command(requires=CanAddBookPolicy)
    def add(self, actor, title, author, reference_only):
        book = author.add_book(title, reference_only)
        emit("book_added", book=book, actor=actor)
        return book

    @command(requires=CanBorrowPolicy)
    def borrow(self, book, actor):
        loan = book.open_loan(actor)
        sync_timers(loan)
        emit("book_borrowed", loan=loan, actor=actor)
        return loan

    @command(requires=CanReservePolicy)
    def reserve(self, book, actor):
        hold = book.place_hold(actor)
        emit("hold_placed", hold=hold, actor=actor)
        return hold

    @command(only_if=ReadyToOfferPolicy)
    def offer_next_hold(self, book):
        hold = book.next_waiting_hold
        hold.offer()
        sync_timers(hold)
        emit("hold_offered", hold=hold)
        return hold


class LoanManager(Manager.from_queryset(LoanQuerySet)):
    @command(requires=CanRenewPolicy, locks=["book"])
    def renew(self, loan, actor, days):
        loan.extend(days)
        sync_timers(loan)
        emit("loan_renewed", loan=loan, actor=actor)
        return loan

    @command(requires=CanCheckInPolicy, locks=["book"])
    def check_in(self, loan, actor):
        loan.close()
        sync_timers(loan)
        emit("loan_returned", loan=loan, actor=actor)
        models.Book.objects.offer_next_hold(loan.book)
        return loan

    @command(only_if=IsOpenCheck)
    def send_due_reminder(self, loan):
        emit("loan_due_soon", loan=loan)
        return loan

    @command(only_if=IsDueCheck, locks=["book"])
    def process_due(self, loan):
        if RenewablePolicy.decide(loan, SYSTEM):
            loan.extend(loan.book.loan_days)
            emit("loan_auto_renewed", loan=loan)
        else:
            loan.mark_overdue()
            emit("loan_overdue", loan=loan)
        sync_timers(loan)
        return loan


class HoldManager(Manager.from_queryset(HoldQuerySet)):
    @command(requires=CanCollectHoldPolicy, locks=["book"])
    def collect(self, hold, actor):
        hold.close()
        loan = hold.book.open_loan(actor)
        sync_timers(hold, loan)
        emit("hold_collected", hold=hold, loan=loan)
        return loan

    @command(only_if=IsOfferedCheck, locks=["book"])
    def expire(self, hold):
        hold.close()
        sync_timers(hold)
        emit("hold_expired", hold=hold)
        models.Book.objects.offer_next_hold(hold.book)
        return hold
```

The example imports the shared classes from `.common` because it lived in its own sandbox. Real apps import from `common`.

### Checks

A check tests one thing and has one reason code. The reason is a snake_case string literal written on the class, and it names what is wrong from the caller's point of view (`on_loan`, `renewal_limit`, `not_holder`). A reason means one thing across the app, and two checks share a reason only when the client would treat them identically. Reasons are part of the API contract, because `Actions` publishes them as an enum and refusals return them as the error code.

Checks used only by `only_if` have no reason, because nobody sees their failure.

A check reads properties of the instance and the actor. Avoid queries inside a check: checks used by `Actions` run for every row of a list response, and properties reading prefetched relations keep that cheap. Checks used only by commands may query when they need to, because they run once, under the lock.

Every check keeps the signature `check(self, instance, actor)`, even when it does not read the actor, because that is the interface `Check.decide` calls.

A check lives in the app that owns the data it queries beyond its target. `HasNoPendingProposalCheck` takes a game but queries draw proposals, so it lives in `draw_proposal`: the phase and game apps must not know about draw proposals. A check that reads only phase state lives in `phase/checks.py`. A check that starts from the game, such as `IsCurrentPhaseActiveCheck`, lives in `game/checks.py`, and so do the shared policies built from those checks.

Constants a check depends on, such as `MAX_RENEWALS`, sit at the top of `checks.py`.

```python
from .common.checks import Check

MAX_RENEWALS = 2


class IsLendableCheck(Check):
    reason = "reference_only"

    def check(self, book, actor):
        return not book.reference_only


class IsOnShelfCheck(Check):
    reason = "on_loan"

    def check(self, book, actor):
        return book.is_on_shelf


class IsOnLoanCheck(Check):
    reason = "on_shelf"

    def check(self, book, actor):
        return not book.is_on_shelf


class HasNoQueueCheck(Check):
    reason = "has_holds"

    def check(self, book, actor):
        return not book.open_holds


class IsNotHoldingCheck(Check):
    reason = "already_holding"

    def check(self, book, actor):
        return all(hold.holder_id != actor.pk for hold in book.open_holds)


class IsNotBorrowingCheck(Check):
    reason = "already_borrowing"

    def check(self, book, actor):
        return book.current_loan is None or book.current_loan.borrower_id != actor.pk


class HasWaitingHoldCheck(Check):
    def check(self, book, actor):
        return book.next_waiting_hold is not None


class HasNoOfferedHoldCheck(Check):
    def check(self, book, actor):
        return not any(hold.is_offered for hold in book.open_holds)


class IsBorrowerCheck(Check):
    reason = "not_borrower"

    def check(self, loan, actor):
        return loan.borrower_id == actor.pk


class IsOpenCheck(Check):
    reason = "already_returned"

    def check(self, loan, actor):
        return loan.is_open


class IsDueCheck(Check):
    def check(self, loan, actor):
        return loan.is_due


class IsBookUnrequestedCheck(Check):
    reason = "book_requested"

    def check(self, loan, actor):
        return not loan.book.open_holds


class IsUnderRenewalLimitCheck(Check):
    reason = "renewal_limit"

    def check(self, loan, actor):
        return loan.renewals < MAX_RENEWALS


class IsHolderCheck(Check):
    reason = "not_holder"

    def check(self, hold, actor):
        return hold.holder_id == actor.pk


class IsOfferedCheck(Check):
    reason = "not_offered"

    def check(self, hold, actor):
        return hold.is_offered
```

### Policies

A policy is an ordered list of checks, and may list another policy directly among them, as `CanRenewPolicy` lists `RenewablePolicy`. List the policy itself, not its `.checks`. A policy used as `requires` is named for the permission it grants (`CanBorrowPolicy`). A policy describing a state that several commands or branches reuse is named for that state (`RenewablePolicy`, `ReadyToOfferPolicy`). A policy is never a mixin on a model, and it has no logic of its own beyond its list.

```python
from .checks import (
    HasNoOfferedHoldCheck,
    HasNoQueueCheck,
    HasWaitingHoldCheck,
    IsBookUnrequestedCheck,
    IsBorrowerCheck,
    IsHolderCheck,
    IsLendableCheck,
    IsNotBorrowingCheck,
    IsNotHoldingCheck,
    IsOfferedCheck,
    IsOnLoanCheck,
    IsOnShelfCheck,
    IsOpenCheck,
    IsUnderRenewalLimitCheck,
)
from .common.checks import IsStaffCheck, SignedInCheck
from .common.policies import Policy


class CanAddBookPolicy(Policy):
    checks = [
        IsStaffCheck,
    ]


class CanBorrowPolicy(Policy):
    checks = [
        SignedInCheck,
        IsLendableCheck,
        IsOnShelfCheck,
        HasNoQueueCheck,
    ]


class CanReservePolicy(Policy):
    checks = [
        SignedInCheck,
        IsLendableCheck,
        IsOnLoanCheck,
        IsNotBorrowingCheck,
        IsNotHoldingCheck,
    ]


class RenewablePolicy(Policy):
    checks = [
        IsOpenCheck,
        IsBookUnrequestedCheck,
        IsUnderRenewalLimitCheck,
    ]


class CanRenewPolicy(Policy):
    checks = [
        IsBorrowerCheck,
        RenewablePolicy,
    ]


class CanCheckInPolicy(Policy):
    checks = [
        IsBorrowerCheck,
        IsOpenCheck,
    ]


class CanCollectHoldPolicy(Policy):
    checks = [
        IsHolderCheck,
        IsOfferedCheck,
    ]


class ReadyToOfferPolicy(Policy):
    checks = [
        IsOnShelfCheck,
        HasNoOfferedHoldCheck,
        HasWaitingHoldCheck,
    ]
```

### Timers and tasks

A timer class names its procrastinate task, the model field holding the job id, and `run_at`. The job id field is a nullable `BigIntegerField` with `editable=False`. The model lists its timers in a `timers` tuple, and commands call `sync_timers` after writes.

A task takes the primary key, calls one command, and does nothing else. The command's `only_if` makes a late or duplicate job harmless, and the command's lock makes it safe to run alongside a user request.

```python
from datetime import timedelta

from .common.timers import Timer

HOLD_COLLECTION_WINDOW = timedelta(days=3)


class DueReminderTimer(Timer):
    task = "library.send_due_reminder"
    job_id_field = "reminder_job_id"

    def run_at(self, loan):
        if not loan.is_open:
            return None
        return loan.due_at - timedelta(days=1)


class DueTimer(Timer):
    task = "library.process_due_loan"
    job_id_field = "due_job_id"

    def run_at(self, loan):
        if not loan.is_open or loan.overdue_at is not None:
            return None
        return loan.due_at


class HoldExpiryTimer(Timer):
    task = "library.expire_hold"
    job_id_field = "expiry_job_id"

    def run_at(self, hold):
        if not hold.is_offered:
            return None
        return hold.offered_at + HOLD_COLLECTION_WINDOW
```

```python
from procrastinate.contrib.django import app

from .models import Hold, Loan
from .timers import DueReminderTimer, DueTimer, HoldExpiryTimer


@app.task(name=DueReminderTimer.task)
def send_due_reminder(pk):
    Loan.objects.send_due_reminder(pk)


@app.task(name=DueTimer.task)
def process_due_loan(pk):
    Loan.objects.process_due(pk)


@app.task(name=HoldExpiryTimer.task)
def expire_hold(pk):
    Hold.objects.expire(pk)
```

### Hydrators and loaders

Each output serializer has one loader, named after the model (`BookLoader`). The loader's queryset joins and prefetches everything the serializer and the properties it reads touch. Prefetches use the QuerySet's named filters, such as `Loan.objects.open()`, so that properties iterating `.all()` see only the rows they expect.

A value that needs its own query per page is a hydrator. A hydrator for an aggregate subclasses `AggregateHydrator`. A hydrator that depends on the actor, such as whether this user has borrowed the book before, subclasses `Hydrator` and handles the anonymous actor.

Every response goes through a loader, including the response of a command, so a field never differs between a list response and an action response.

```python
from django.db.models import Count

from .common.hydrators import AggregateHydrator, Hydrator
from .models import Loan


class TimesBorrowedHydrator(AggregateHydrator):
    attribute = "times_borrowed"
    queryset = Loan.objects.all()
    key = "book_id"
    value = Count("id")
    default = 0


class BorrowedBeforeHydrator(Hydrator):
    def hydrate(self, books, actor):
        borrowed = set()
        if actor.is_authenticated:
            borrowed = set(Loan.objects.filter(borrower=actor, book__in=books).values_list("book_id", flat=True))
        for book in books:
            book.borrowed_before = book.pk in borrowed
```

```python
from django.db.models import Prefetch

from .common.loaders import Loader
from .hydrators import BorrowedBeforeHydrator, TimesBorrowedHydrator
from .models import Author, Book, Hold, Loan


class BookLoader(Loader):
    queryset = Book.objects.select_related("author").prefetch_related(
        Prefetch("loans", queryset=Loan.objects.open()),
        Prefetch("holds", queryset=Hold.objects.open()),
    )
    hydrators = [
        TimesBorrowedHydrator(),
        BorrowedBeforeHydrator(),
    ]


class AuthorLoader(Loader):
    queryset = Author.objects.all()
    nested = {"books": BookLoader}


class LoanLoader(Loader):
    queryset = Loan.objects.select_related("book").prefetch_related(
        Prefetch("book__holds", queryset=Hold.objects.open()),
    )


class HoldLoader(Loader):
    queryset = Hold.objects.select_related("book")
```

### Filters

A list endpoint that accepts query parameters has a FilterSet. A boolean parameter whose meaning is a named set of rows uses `QuerySetFilter` with the QuerySet method's name. Plain field filters use django-filter's own filter classes. `fields = ()` keeps django-filter from generating filters the endpoint did not ask for.

```python
from django_filters import rest_framework as filters

from .common.filters import QuerySetFilter
from .models import Book, Loan


class BookFilterSet(filters.FilterSet):
    on_shelf = QuerySetFilter("on_shelf")
    author = filters.NumberFilter(field_name="author_id")

    class Meta:
        model = Book
        fields = ()


class LoanFilterSet(filters.FilterSet):
    open = QuerySetFilter("open")

    class Meta:
        model = Loan
        fields = ()
```

### Serializers

All of an app's serializers are in one `serializers.py`.

An input serializer is named `XInputSerializer`, after the operation (`RenewLoanInputSerializer`). It validates shape: types, choices, lengths, and that referenced rows exist. It does not check business rules, read the actor or write anything. Its validated values become the keyword arguments of the view's `perform`, so its field names match the command's parameter names.

An output serializer is named `XOutputSerializer`, after the model, extends `OutputSerializer`, and names its loader in `Meta.loader`. Its fields read model fields, properties and hydrated attributes. It does not query: a value that would need a `SerializerMethodField` with a query is a property over prefetched data or a hydrator. An `Actions` field lists the commands a client may offer on the row.

Serializer class names become OpenAPI component names and generated TypeScript type names. When a converted app already has published component names, keep them with drf-spectacular's `extend_schema_serializer(component_name=...)` rather than renaming the wire types.

```python
from rest_framework import serializers

from .common.serializers import Actions, OutputSerializer
from .loaders import AuthorLoader, BookLoader, HoldLoader, LoanLoader
from .models import Author, Book, Hold, Loan


class AddBookInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    reference_only = serializers.BooleanField(default=False)


class RenewLoanInputSerializer(serializers.Serializer):
    days = serializers.ChoiceField(choices=[7, 14])


class BookOutputSerializer(OutputSerializer):
    author = serializers.CharField(source="author.name")
    on_shelf = serializers.BooleanField(source="is_on_shelf")
    times_borrowed = serializers.IntegerField()
    borrowed_before = serializers.BooleanField()
    actions = Actions(borrow=Book.objects.borrow, reserve=Book.objects.reserve)

    class Meta:
        model = Book
        loader = BookLoader
        fields = ("id", "title", "author", "on_shelf", "times_borrowed", "borrowed_before", "actions")


class AuthorOutputSerializer(OutputSerializer):
    books = BookOutputSerializer(many=True)

    class Meta:
        model = Author
        loader = AuthorLoader
        fields = ("id", "name", "books")


class LoanOutputSerializer(OutputSerializer):
    title = serializers.CharField(source="book.title")
    actions = Actions(renew=Loan.objects.renew, check_in=Loan.objects.check_in)

    class Meta:
        model = Loan
        loader = LoanLoader
        fields = ("id", "title", "due_at", "renewals", "overdue_at", "returned_at", "actions")


class HoldOutputSerializer(OutputSerializer):
    title = serializers.CharField(source="book.title")
    actions = Actions(collect=Hold.objects.collect)

    class Meta:
        model = Hold
        loader = HoldLoader
        fields = ("id", "title", "offered_at", "closed_at", "actions")
```

### Views

A view is declarations plus, for a write, a `perform` method that calls one command. `perform` receives the target (for `ActionView`) and the validated input values. It passes `self.request.user` as the actor and returns the command's result.

Read endpoints are `LoaderListView` or `LoaderDetailView`. Write endpoints are `ActionView`, or `CreateActionView` for creation. A list view with a FilterSet declares `filter_backends = [DjangoFilterBackend]` beside its `filterset_class`. `permission_classes` hold only rules about the user alone, as described in the placement rules above, and every other rule is in the command's policy.

A view does not catch exceptions, build responses, open transactions or emit events.

The example views have no docstrings. In this codebase, DRF view docstrings become operation descriptions in the OpenAPI schema, so removing them from existing views changes the schema. Converted apps keep the docstrings their views already have.

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated

from .common.views import ActionView, CreateActionView, LoaderDetailView, LoaderListView
from .filters import BookFilterSet, LoanFilterSet
from .models import Book, Hold, Loan
from .serializers import (
    AddBookInputSerializer,
    AuthorOutputSerializer,
    BookOutputSerializer,
    HoldOutputSerializer,
    LoanOutputSerializer,
    RenewLoanInputSerializer,
)


class BookListView(LoaderListView):
    permission_classes = [AllowAny]
    serializer_class = BookOutputSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookFilterSet


class BookCreateView(CreateActionView):
    permission_classes = [IsAuthenticated]
    input_serializer_class = AddBookInputSerializer
    serializer_class = BookOutputSerializer

    def perform(self, title, author, reference_only):
        return Book.objects.add(self.request.user, title, author, reference_only)


class BookBorrowView(ActionView):
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = LoanOutputSerializer

    def perform(self, book):
        return Book.objects.borrow(book, self.request.user)


class BookReserveView(ActionView):
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = HoldOutputSerializer

    def perform(self, book):
        return Book.objects.reserve(book, self.request.user)


class AuthorDetailView(LoaderDetailView):
    permission_classes = [AllowAny]
    serializer_class = AuthorOutputSerializer


class LoanListView(LoaderListView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanOutputSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoanFilterSet


class LoanRenewView(ActionView):
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()
    input_serializer_class = RenewLoanInputSerializer
    serializer_class = LoanOutputSerializer

    def perform(self, loan, days):
        return Loan.objects.renew(loan, self.request.user, days)


class LoanCheckInView(ActionView):
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()
    serializer_class = LoanOutputSerializer

    def perform(self, loan):
        return Loan.objects.check_in(loan, self.request.user)


class HoldCollectView(ActionView):
    permission_classes = [IsAuthenticated]
    queryset = Hold.objects.all()
    serializer_class = LoanOutputSerializer

    def perform(self, hold):
        return Hold.objects.collect(hold, self.request.user)
```

```python
from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/create/", views.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/borrow/", views.BookBorrowView.as_view(), name="book-borrow"),
    path("books/<int:pk>/reserve/", views.BookReserveView.as_view(), name="book-reserve"),
    path("authors/<int:pk>/", views.AuthorDetailView.as_view(), name="author-detail"),
    path("loans/", views.LoanListView.as_view(), name="loan-list"),
    path("loans/<int:pk>/renew/", views.LoanRenewView.as_view(), name="loan-renew"),
    path("loans/<int:pk>/check-in/", views.LoanCheckInView.as_view(), name="loan-check-in"),
    path("holds/<int:pk>/collect/", views.HoldCollectView.as_view(), name="hold-collect"),
]
```

### Tests

Tests are written alongside the code, and the shared classes are tested through the app that first uses them rather than with synthetic models. Command behaviour is tested two ways. Endpoint tests cover the status codes and response bodies the client sees. Direct manager calls cover system-triggered commands, `only_if` skipping, and commands called from other apps. Test setup that needs a state the commands would refuse, such as two pending proposals in one phase, builds it with factories rather than by calling commands.

## Converting an existing app

A conversion changes the code's structure, not what the API does. Shipped mobile builds depend on the current API, so a converted app keeps its URLs, URL names, HTTP methods, request and response bodies, and OpenAPI schema. Status codes of refusals may change, because every refusal now answers 403. Clients treat refusals as generic errors, so this is accepted. The rules that follow are:

1. The app's existing endpoint tests pass. Three kinds of change to them are allowed: updating calls to internal methods to the new command names, changing the expected status of a refusal to 403, and moving test setup that the new policies would refuse onto factories.
2. Regenerating the OpenAPI schemas (`docker compose up codegen`, configured as described in `.claude/rules/backend/codegen.md`) produces no diff, and `npx tsc -b --noEmit` passes in `packages/web`.
3. Converted write endpoints are action views, and they keep the existing schema. The view declares the existing endpoint's methods with `http_method_names`. Where the published schema differs from what `ActionSchema` describes, such as a request body on a create endpoint that takes no input, or a response component the endpoint does not really return, the view keeps the published schema with `@extend_schema`.
4. Existing serializer component names are kept with `extend_schema_serializer(component_name=...)`.
5. Every caller of the app's old internal methods in other apps is updated in the same change.
6. Only the shared classes the app uses are added.

## Converting draw_proposal

`draw_proposal` is the first app to convert. This section records what the analysis of the current app found, and the intended shape. It is a starting point for the implementation rather than a finished design, and the implementer should confirm each point against the code.

### Current behaviour that must be preserved

The app exposes four endpoints under `games/<game_id>/draw-proposals/`:

1. A list, `GET`, returning `DrawProposal` items.
2. Create, `POST` to `create/`, which publishes a `DrawProposal` request body and returns 201 with the new proposal.
3. Vote, `PUT` and `PATCH` to `<proposal_id>/vote/`. These publish `DrawVoteUpdate` as both the request and the response schema, although the response body is actually a `DrawProposal`.
4. Cancel, `DELETE` to `<proposal_id>/cancel/`, returning 204.

The generated frontend client depends on these operation ids and the component names `DrawProposal`, `DrawVoteUpdate`, `DrawVoteMember` and `MyVote`, so all four stay as they are, including the inaccurate vote response schema.

Today the rules are split across three places:

1. Permission classes from `common/permissions.py` answer 403. They check that the game is active, that the user is an active player (`IsActiveGamePlayer`: a player member that is neither eliminated nor vacant), that the game is not a sandbox, and that the current phase is active. The list endpoint uses `IsActiveOrCompletedGame` instead.
2. Serializer validation and view code answer 400 for the state rules. These are: the member already has an active proposal this phase, another proposal is pending this phase, the phase stopped being active after locking, the proposal is not pending, the member has no vote, and the member already voted.
3. Cancelling a proposal the member did not create, or one already cancelled, answers 404, because the cancel view's lookup filters on the creator.

After conversion, the rules in the first two groups are all checks, and every refusal answers 403 with a reason code. The tests that assert 400 for a refusal change to 403. The cancel lookup no longer filters on the creator or on cancellation, so cancelling someone else's proposal answers 403 `not_proposer`, and cancelling one already cancelled answers 403 `not_pending`. Write lookups only find proposals in the URL's game. A 400 remains only for an invalid body, such as a vote without `accepted`.

The frontend shows a generic toast on any error and does not read the error body. Refusal bodies can therefore change from DRF's message lists to `{"code": reason}`, and statuses can change from 400 to 403.

The list response is computed from prefetched votes, and a test asserts that the query count does not grow with the number of proposals. `my_vote` depends on the requesting user's member in the game.

### Callers outside the app

The app's internal methods are used elsewhere, and each of these callers moves to the new commands in the same change:

1. The member app's withdrawal calls `apply_withdrawal(member, phase)` inside its own transaction, after locking the active phase.
2. The notification registry calls `pending_for_phase`, which stays as a QuerySet method.
3. Tests in the member, notification and game apps, and the `seed_staging` management command, call `create_proposal(game=..., created_by=member)` and `process_acceptance()` directly.

One notification test creates two proposals in the same phase through `create_proposal`. The propose policy refuses the second one, so that test's setup moves to `draw_proposal_factory`.

### Intended shape

The actor is the user, as everywhere else. The acting member is the game's member whose user is the actor, found the same way `CurrentGameMemberMixin` finds it.

The game-level rules that are permission classes today become checks shared by every draw proposal command. These are an active game, not a sandbox, an active current phase, and the actor being an active player. Each check reads the game through `game_of(instance)`, so the same checks work whether the target is the game or a proposal. They are grouped into one shared policy that each command's policy lists first. They live in the game app, as `game/checks.py` and `game/policies.py`, new modules alongside the unconverted game code.

`IsActiveGamePlayer` currently has one message per way of failing. As checks, it splits into one check per reason, for example one for not being a player in the game and one for having no seat that is still active. The implementer picks the split and the reason codes.

Reads have no policy. The list endpoint's rule that the game is active or finished becomes part of `DrawProposalQuerySet.visible_to`, filtering on the game's status. A list for a game in any other state is then empty rather than a 403. Games in those states have no phases, and so no proposals, so this changes nothing in practice.

Proposed commands on the draw proposal manager:

1. `propose(game, actor)` targets the game, which the view already has from `SelectedGameMixin`, and locks the game's current phase with `locks=["current_phase"]`, replacing the current `lock_if_active` call. Phase resolution locks the phase row, so this serializes proposing with resolution. After the shared game policy, which checks that the current phase is active, its policy checks that the actor has no active proposal in the current phase and that no other proposal in it is pending. The body creates the proposal in the current phase, creates its votes with `create_initial_votes`, emits `draw_proposal`, and calls `conclude`.
2. `vote(proposal, actor, accepted)` locks `phase` and then the proposal. After the shared game policy, its policy checks that the proposal is pending, that the actor has a vote, and that the vote has not been cast. The body records the vote, emits `draw_proposal_rejected` if the proposal is now rejected, and calls `conclude`.
3. `cancel(proposal, actor)` requires the shared game policy without the active phase check, which the cancel endpoint does not apply today, and requires the actor to be the proposer and the proposal to be pending. It sets `cancelled_at` through a model write method.
4. `conclude(proposal)` replaces `process_acceptance`. It locks `phase` and has an `only_if` policy that the proposal is accepted and its phase is active, so it returns `None` in the cases where `process_acceptance` returned `None` today. `propose`, `vote` and `release_member` call it without a condition. The body calls `game.finish_with_draw(phase, members)` with the proposal's phase and included members, which records the victory, marks the members who drew and finishes the game, and then emits the game-ended event. The game method takes plain values rather than the proposal, so the game app does not depend on draw proposals.
5. `release_member(phase, member)` replaces `apply_withdrawal`. It is a system command whose member is an input rather than the actor. It cancels the member's own pending proposals, releases the member's vote on the others, and calls `conclude` for each. The member-withdrawal command itself will live in the member or game app, but this part stays in `draw_proposal` because it writes draw proposal rows.

All write paths lock the phase before any proposal. Today's withdrawal already holds the phase lock when it reaches the draw proposal code, so this order avoids a deadlock between a withdrawal and a concurrent vote, and it is the reason `lock_rows` locks paths before the target. Locking the proposal in `vote` and `cancel` also closes the window where a vote and a cancellation, or two final votes, can interleave today.

Because a command re-fetches its target under the lock, the target has no prefetch cache. The current workaround of deleting `_prefetched_objects_cache` before recomputing the status is no longer needed.

The serializer's sandbox validation duplicates `IsNotSandboxGame`, and both become the one sandbox check.

The current `with_related_data` becomes the `DrawProposalLoader` queryset, and the list, create and vote responses all go through it. The count fields become model properties over the prefetched votes. `my_vote` needs the requesting user. It becomes a hydrator, or stays a serializer method reading prefetched votes and the member from the serializer context; the implementer should choose whichever keeps the schema and the query count test unchanged.

The list is a `LoaderListView`, create is a `CreateActionView`, and vote and cancel are `ActionView`s. Vote declares `http_method_names = ["put", "patch", "options"]` and cancel `["delete", "options"]`. Both look the proposal up with `lookup_url_kwarg = "proposal_id"` in a queryset filtered to the URL's game. `permission_classes = [IsAuthenticated]` is every view's only permission, and each `perform` calls one command. The create view keeps its published `DrawProposal` request body, and the vote view its published `DrawVoteUpdate` response, with `@extend_schema`. The output and vote serializers keep their published component names.
