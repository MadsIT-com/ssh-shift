# Security policy

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue. Use the
repository's private GitHub security-advisory reporting feature. If that
feature is unavailable, open an issue containing no sensitive details and ask
the maintainers for a private contact channel.

## Security model

SSHShift is a graphical launcher for the system OpenSSH client. It does not
implement SSH, authentication, cryptography, or a terminal emulator. OpenSSH
runs inside Konsole and communicates directly with the remote service.

SSHShift does not collect passwords. OpenSSH obtains passwords, key
passphrases, hardware-token confirmations, and other authentication input from
the terminal or its normal helpers.

Connection fields and advanced options are session-only. They are written to a
mode-0600 configuration inside a mode-0700 directory under `/run/user/$UID`,
which is normally tmpfs. Konsole and OpenSSH receive the private configuration
path plus a fixed alias, so destination names are not placed in their command
arguments. The directory is removed when the terminal session ends.

The persistent known-host file contains public host keys under an opaque HMAC
of the normalized hostname and port using a random secret held in KDE Wallet.
This prevents an offline hostname-guessing attack against the known-host file
alone.

For readable OpenSSH prompts, SSHShift translates matching host keys into a
mode-0600 known-hosts file inside the private runtime directory. It contains the
real destination only while the session is active. After Konsole exits, the
entries are translated back to their opaque identities under an exclusive lock
and written atomically before the runtime directory is removed.

Host-key trust uses OpenSSH's `StrictHostKeyChecking ask` behavior. A new key
requires confirmation, an unchanged key connects normally, and a changed key
is refused. Do not bypass a changed-key warning without independently
verifying the replacement fingerprint.

## Important limitations

- Destination names necessarily exist in SSHShift and OpenSSH process memory
  while a connection is active.
- OpenSSH errors or remote shell output may contain destination information in
  the visible Konsole scrollback.
- A process running as the same user while KDE Wallet is unlocked may be able
  to request the privacy key or inspect process memory and runtime files.
- A privileged attacker can inspect memory, network state, DNS traffic, and
  the encrypted machine as it runs.
- DNS infrastructure, network observers, jump hosts, and destination systems
  necessarily learn information required to route the connection.
- Agent and X11 forwarding expand the trust placed in a remote host. They are
  disabled by default and should be enabled only when needed.
- OpenSSH remains responsible for cryptographic and protocol security.
