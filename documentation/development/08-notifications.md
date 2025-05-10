# Notifications

## Overview

The service provides notifications to users for the following events:

1. A game that they are a member of has started.
2. They have received a message in a channel.
3. A phase in a game that they are an active member of has resolved.

Notifications are sent via Firebase Cloud Messaging (FCM) for web, Android, and
iOS users, and via email using Azure Communication Services.

## Implementation

### Firebase Cloud Messaging (FCM)

We use the `django-fcm` library to integrate with FCM for sending push
notifications. Each user device is registered with an FCM token, which is stored
in the `FCM_DEVICE` table in the database.

#### Workflow

1. When an event occurs (e.g., game start, message received, phase resolved), a
   task is added to the Celery task queue.
2. The task retrieves the relevant FCM tokens for the relevant users from the
   `FCM_DEVICE` table.
3. The task sends a push notification to the users via FCM.

### Email Notifications

We use Azure Communication Services to send email notifications. By default,
email notifications are enabled for all users, but users can disable them in
their account settings.

#### Workflow

1. When an event occurs, a task is added to the Celery task queue.
2. The task retrieves the email addresses of the relevant users from the
   database.
3. The task sends an email notification to the users via Azure Communication
   Services.

## User Preferences

Users can manage their notification preferences, including enabling or disabling
email notifications, through their account settings. Push notifications cannot
be disabled but require users to register their devices.

## Testing

Two `manage.py` commands are provided to test the notification system:

```bash
python manage.py test_push_notifications --token <FCM_TOKEN>
```

```bash
python manage.py test_email_notifications --email <EMAIL_ADDRESS>
```
