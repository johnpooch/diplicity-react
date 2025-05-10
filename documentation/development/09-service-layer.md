# Service Layer

## Overview

The service layer is a design pattern that acts as an intermediary between the
views and the data access layer (models). It encapsulates business logic,
ensuring that the views remain lightweight and focused on handling HTTP requests
and responses.

By centralizing business logic in the service layer, the architecture becomes
more modular, testable, and maintainable.

**Note**: https://forum.djangoproject.com/t/show-wireup-modern-dependency-injection-for-django/31535

https://maldoinc.github.io/wireup/latest/integrations/django/

## Example

```python
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from .services.message_service import MessageService

class CreateMessageView(APIView):
    def post(self, request):
        user = request.user
        content = request.data.get('content')

        message = MessageService.create_message(user, content)

        return Response({'message': 'Message created successfully', 'message_id': message.id})
```

```python
# services/message_service.py

from django.db import transaction
from .models import Message
from .tasks import send_notification, send_email

class MessageService:
    @staticmethod
    def create_message(user, content):
        with transaction.atomic():
            # Create the message instance
            message = Message.objects.create(user=user, content=content)

            # Add notification task to the queue
            send_notification.delay(user.id, message.id)

            # Add email task to the queue
            send_email.delay(user.email, message.id)

        return message
```
