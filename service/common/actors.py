class SystemActor:
    pk = None
    is_authenticated = True
    is_staff = False


SYSTEM = SystemActor()


def scoped(queryset, actor):
    if actor is SYSTEM:
        return queryset
    return queryset.visible_to(actor)
