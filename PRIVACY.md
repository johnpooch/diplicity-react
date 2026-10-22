# Privacy Policy

**Last updated:** October 22, 2026

Diplicity is a mobile and web application for playing the classic Diplomacy board game online. This privacy policy explains what data we collect, how we use it, and your rights regarding that data.

Diplicity is developed and maintained by John McDowell (individual developer).

## 1. Information We Collect

### Account Information

You can create an account with an email address and password, or sign in with Google or Apple.

When you sign in with Google, we receive and store:

- **Name** — your Google account display name
- **Email address** — your Google account email
- **Profile picture URL** — a link to your Google profile photo, used unless you upload your own picture

When you sign in with Apple, we receive and store:

- **Email address** — the email Apple shares with us, which may be a private relay address if you chose "Hide My Email"
- **Name** — the first and last name Apple shares on your first sign-in, if you choose to share it

We do not access your Google or Apple password, contacts, or any other data in those accounts.

When you register with an email address and password, we store:

- **Email address** — used to sign in and to send you account emails
- **Password** — stored only as a salted one-way hash; we cannot read it
- **Display name** — the name you choose for other players to see

### Account Emails

We send email only to verify a new email/password account and to reset a password you have asked to reset. These emails are delivered by Resend, which receives your email address and the content of the message. We do not send marketing email.

### Profile Pictures

You can upload your own picture to replace the one from your Google account. If you do:

- **We store the image ourselves**, on the same infrastructure that runs the app — it is not sent to a third-party image host
- **We re-encode it on upload.** The image is resized, cropped to a square, and written back out from raw pixel data, which discards all embedded metadata. That includes EXIF GPS coordinates, so if you upload a photo taken on a phone, the location it was taken in is not stored or served
- **The picture is served from an unauthenticated URL.** The address of your picture has to be loadable without signing in, so anyone who has the link can view the image. Treat a picture you upload as public
- **Your picture is visible to other players** in games you join, in game chat, and on your public profile. In anonymous games it is hidden from other players, along with your name, until the game finishes

We accept JPEG, PNG and WebP images. Uploading a picture is optional; you can remove it at any time from the Account screen.

### Gameplay Data

When you use the app, we store:

- **Game state** — games you create or join, game settings, and phase history
- **Orders** — the moves you submit during gameplay
- **Chat messages** — messages you send in game chat channels
- **Channel membership** — which chat channels you participate in
- **AI bot activity** — in games with an AI bot player, the information sent to Anthropic for each bot decision or reply, and the response, kept with the game

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
- **Run computer-controlled players** — when a game includes an AI bot player, information about the game is sent to Anthropic to decide the bot's moves and replies (see Third-Party Services below)
- **Deliver notifications** about game events you've opted into
- **Monitor application health** — detect errors and performance issues (see Third-Party Services below)

We do **not** use your data for advertising, analytics profiling, or cross-app tracking.

## 3. Third-Party Services

We use the following third-party services:

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| **Google Sign-In** | Authentication | Name, email, profile picture (received from Google) |
| **Sign in with Apple** | Authentication | Email (possibly a private relay address) and, on first sign-in, name (received from Apple) |
| **Resend** | Account emails (verification and password reset) | Your email address and the email's content |
| **Anthropic** | Computer-controlled (AI bot) players | For games that include an AI bot player: the game state (board, units, nations and available orders) and the chat messages in channels the bot is a member of, labelled with the sender's nation. A channel's name can include a game master's display name. Your email address and account details are not sent. |
| **Railway** | Hosting for the backend and its PostgreSQL database | All data described in this policy is stored on Railway's infrastructure |
| **Cloudflare R2** | Storing and delivering mobile app update bundles | No account data; when the app downloads an update, Cloudflare receives the request, including your IP address |
| **Firebase Cloud Messaging** | Push notifications | FCM device tokens |
| **Sentry** | Error tracking | Error reports with PII masked; no authentication headers or credentials are sent |
| **Honeycomb (OpenTelemetry)** | Performance monitoring | Request traces and timing data; no user-identifiable information |

We do not sell or share your personal data with any other third parties.

Chat messages sent in a channel that includes an AI bot player are processed by Anthropic so the bot can reply. If you do not want your messages processed this way, do not send them in a channel that includes a bot.

## 4. Data Storage & Security

- All data is transmitted over HTTPS/TLS
- The backend runs on Railway's infrastructure with managed PostgreSQL
- Authentication uses industry-standard JWT tokens
- Profile picture URLs are the one exception to authenticated access — see Profile Pictures above
- We follow security best practices but cannot guarantee absolute security — no system is 100% secure

## 5. Data Retention & Deletion

### How long we keep your data

- **Account data** is retained as long as your account exists
- **Gameplay data** (games, orders, messages) is retained indefinitely as part of the game record
- **FCM device tokens** are removed when you sign out or disable notifications
- **Uploaded profile pictures** are kept until you remove your picture or delete your account; the stored image file is deleted in both cases

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

This holds for pictures you upload too. A photo taken on a phone often carries the location it was taken in as EXIF metadata; that metadata is discarded when we re-encode the picture, so it is never stored or served.

## 7. Children's Privacy

Diplicity is not directed at children under 13. We do not knowingly collect personal information from children under 13. If you believe a child under 13 has provided us with personal data, please contact us so we can remove it.

## 8. Changes to This Policy

We may update this policy from time to time. Changes will be reflected by updating the "Last updated" date at the top. Continued use of the app after changes constitutes acceptance of the updated policy.

## 9. Contact

For privacy-related questions or concerns, open an issue at [github.com/johnpooch/diplicity-react/issues](https://github.com/johnpooch/diplicity-react/issues) or contact the developer directly through GitHub.
