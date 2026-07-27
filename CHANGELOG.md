# Changelog

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
