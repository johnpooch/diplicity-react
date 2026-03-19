# Privacy Policy

**Last updated:** March 18, 2026

Diplicity is a mobile and web application for playing the classic Diplomacy board game online. This privacy policy explains what data we collect, how we use it, and your rights regarding that data.

Diplicity is developed and maintained by John McDowell (individual developer).

## 1. Information We Collect

### Account Information

When you sign in with Google, we receive and store:

- **Name** — your Google account display name
- **Email address** — your Google account email
- **Profile picture URL** — a link to your Google profile photo

We do not access your Google password, contacts, or any other Google account data.

### Gameplay Data

When you use the app, we store:

- **Game state** — games you create or join, game settings, and phase history
- **Orders** — the moves you submit during gameplay
- **Chat messages** — messages you send in game chat channels
- **Channel membership** — which chat channels you participate in

### Device Tokens

If you enable push notifications, we store your **Firebase Cloud Messaging (FCM) device token** to deliver notifications about game events (e.g., new phases, messages).

### Client-Side Storage

The app stores the following in your browser's local storage or device storage:

- JWT authentication tokens (access and refresh)
- Your name and email (for display purposes)

This data stays on your device and is cleared when you sign out.

## 2. How We Use Your Information

We use your data to:

- **Authenticate you** and maintain your session
- **Run the game** — process orders, resolve phases, manage game membership
- **Deliver notifications** about game events you've opted into
- **Monitor application health** — detect errors and performance issues (see Third-Party Services below)

We do **not** use your data for advertising, analytics profiling, or cross-app tracking.

## 3. Third-Party Services

We use the following third-party services:

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| **Google OAuth** | Authentication | Name, email, profile picture (received from Google) |
| **Firebase Cloud Messaging** | Push notifications | FCM device tokens |
| **Sentry** | Error tracking | Error reports with PII masked; no authentication headers or credentials are sent |
| **Honeycomb (OpenTelemetry)** | Performance monitoring | Request traces and timing data; no user-identifiable information |

We do not sell or share your personal data with any other third parties.

## 4. Data Storage & Security

- All data is transmitted over HTTPS/TLS
- The backend runs on Railway's infrastructure with managed PostgreSQL
- Authentication uses industry-standard JWT tokens
- We follow security best practices but cannot guarantee absolute security — no system is 100% secure

## 5. Data Retention & Deletion

### How long we keep your data

- **Account data** is retained as long as your account exists
- **Gameplay data** (games, orders, messages) is retained indefinitely as part of the game record
- **FCM device tokens** are removed when you sign out or disable notifications

### Account deletion

You can request deletion of your account and all associated personal data by opening an issue at [github.com/johnpooch/diplicity-react/issues](https://github.com/johnpooch/diplicity-react/issues) with the subject "Account Deletion Request." Include the email address associated with your account.

Upon deletion:

- Your account, profile information, and device tokens will be permanently removed
- Gameplay data (orders, messages) in completed games may be retained in anonymized form to preserve game history for other players

We will process deletion requests within 30 days.

## 6. What We Don't Collect

Diplicity does **not** collect or access:

- Location data
- Contacts
- Camera or microphone
- Health or fitness data
- Payment or financial information
- Browsing history or cross-app tracking data
- Advertising identifiers

## 7. Children's Privacy

Diplicity is not directed at children under 13. We do not knowingly collect personal information from children under 13. If you believe a child under 13 has provided us with personal data, please contact us so we can remove it.

## 8. Changes to This Policy

We may update this policy from time to time. Changes will be reflected by updating the "Last updated" date at the top. Continued use of the app after changes constitutes acceptance of the updated policy.

## 9. Contact

For privacy-related questions or concerns, open an issue at [github.com/johnpooch/diplicity-react/issues](https://github.com/johnpooch/diplicity-react/issues) or contact the developer directly through GitHub.
