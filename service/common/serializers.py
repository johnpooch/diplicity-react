from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    pass


class OutputSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields
