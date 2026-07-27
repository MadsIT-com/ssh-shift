# Changelog

## 0.5.0 - 2026-07-27

- Added `username@host` and optional-port notation for destinations and jump
  hosts, while retaining separate username fields.
- Moved jump-host routing to a dedicated optional card on the main screen.
- Refined the native KDE layout, spacing, window sizing, and session title.
- Added visible, cancellable feedback while Konsole starts.
- Kept real destination names out of persistent host-key storage while showing
  readable OpenSSH trust and authentication prompts.
- Added private per-session known-host translation with locked, atomic updates
  to the opaque persistent trust database.
- Preserved compatibility with trust entries written by SSHShift 0.1.0.
- Expanded validation for destination parsing, interface behavior, host-key
  migration, runtime privacy, and launcher arguments.

## 0.1.0 - 2026-07-27

- Added a native Qt 6/KDE one-shot OpenSSH connection dialog.
- Added optional identity-file and jump-host support.
- Added opt-in SSH-agent and untrusted X11 forwarding.
- Added an equivalent-command preview to help users learn OpenSSH syntax.
- Launched OpenSSH in a normal Konsole window with authentication handled by
  OpenSSH itself.
- Kept connection fields in a private runtime configuration rather than
  process arguments or profiles.
- Added KDE-Wallet-keyed opaque host aliases and a dedicated hashed known-host
  database.
- Added automated validation for parsing, privacy defaults, runtime file
  permissions, OpenSSH configuration, and UI behavior.
