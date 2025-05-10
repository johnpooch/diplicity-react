from rest_framework import serializers


def create_serializer_class(name, fields, extra_methods=None):
    extra_methods = extra_methods or {}
    return type(name, (serializers.Serializer,), {**fields, **extra_methods})


def inline_serializer(
    *, fields, data=None, extra_methods=None, name="DynamicSerializer", **kwargs
):
    serializer_class = create_serializer_class(
        name=name, fields=fields, extra_methods=extra_methods
    )

    if data is not None:
        return serializer_class(data=data, **kwargs)

    return serializer_class(**kwargs)
