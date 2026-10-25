from contextlib import contextmanager

from django.db import connection
from rest_framework import serializers
from rest_framework.serializers import LIST_SERIALIZER_KWARGS, LIST_SERIALIZER_KWARGS_REMOVE


class EmptySerializer(serializers.Serializer):
    pass


class QueriesDisabled(Exception):
    pass


def _refuse_query(execute, sql, params, many, context):
    raise QueriesDisabled(sql)


@contextmanager
def queries_disabled():
    with connection.execute_wrapper(_refuse_query):
        yield


class OutputListSerializer(serializers.ListSerializer):
    @property
    def data(self):
        if self.parent is not None:
            return super().data
        with queries_disabled():
            return super().data


class OutputSerializer(serializers.ModelSerializer):
    loader = None

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {key: kwargs.pop(key) for key in LIST_SERIALIZER_KWARGS_REMOVE if kwargs.get(key) is not None}
        list_kwargs["child"] = cls(*args, **kwargs)
        list_kwargs.update({key: value for key, value in kwargs.items() if key in LIST_SERIALIZER_KWARGS})
        list_serializer_class = getattr(getattr(cls, "Meta", None), "list_serializer_class", OutputListSerializer)
        return list_serializer_class(*args, **list_kwargs)

    @property
    def data(self):
        if self.parent is not None:
            return super().data
        with queries_disabled():
            return super().data
