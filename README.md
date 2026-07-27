# SSHShift

**Shift from Windows key → PuTTY → Enter → host → Enter to Debian's
OpenSSH—without a hard landing.**

SSHShift is a profile-free KDE launcher for OpenSSH, built for Windows
administrators moving their daily work to Debian. It provides a familiar
“enter a host and connect” window, then gets out of the way and lets the
system's real `ssh` client run inside Konsole.

SSHShift is part of the **Shift** suite:

- [RDPShift](https://github.com/MadsIT-com/rdp-shift) — an `mstsc`-style,
  profile-free RDP launcher for KDE.
- **SSHShift** — a one-shot graphical launcher for OpenSSH.

The current target is Debian 13 with KDE Plasma and Wayland.

## Why it exists

Debian already ships excellent administration tools, but a command prompt can
be an unnecessarily abrupt first step for administrators arriving from
Windows. SSHShift provides a softer landing without replacing OpenSSH,
inventing a new protocol stack, or locking users into its interface.

The Advanced options panel shows the equivalent `ssh` command for the current
choices. The launcher can therefore act as training wheels: use the graphical
workflow today and take the same command to a terminal whenever you are ready.

## Behavior and privacy

- No connection profiles, recent-host list, saved usernames, or saved
  passwords.
- Authentication is performed directly by OpenSSH in Konsole. SSHShift never
  asks for or handles the password.
- The hostname, username, jump host, and options are supplied through a private
  OpenSSH configuration under `/run/user/$UID`, not command-line arguments.
- The private runtime directory is removed when the Konsole session ends.
- Host-key lookup uses a keyed HMAC of the normalized hostname and port as an
  opaque `HostKeyAlias`.
- The random HMAC key is held in KDE Wallet.
- Known-host aliases are additionally stored with OpenSSH's `HashKnownHosts`.
- OpenSSH asks before trusting a host for the first time, silently accepts an
  unchanged key, and refuses a changed key.
- SSH agent and X11 forwarding are off by default and reset after each launch.
- An explicitly selected identity file and jump host apply only to the current
  connection.

The persistent known-host database is stored at
`$XDG_DATA_HOME/ssh-shift/known_hosts`, normally
`~/.local/share/ssh-shift/known_hosts`. It contains public host keys indexed by
salted hashes of KDE-Wallet-keyed opaque aliases—not server names.

## Installation on Debian 13

Install the runtime dependencies:

```sh
sudo apt install openssh-client konsole python3-dbus python3-pyqt6
```

Then install SSHShift for the current user:

```sh
./install.sh
```

The application appears as **SSHShift** in Plasma's application menu. The
installer defaults to `~/.local`; set `PREFIX` to choose another user prefix.

To uninstall the launcher:

```sh
./uninstall.sh
```

Uninstalling deliberately preserves the known-host database and KDE Wallet key
so reinstalling does not silently discard host-key-change protection.

## Advanced options

- **Identity file:** selects one private key for this connection. When empty,
  OpenSSH uses its normal default keys and SSH agent.
- **Jump host:** routes through a bastion using OpenSSH `ProxyJump`; its identity
  is protected in the same known-host database.
- **Agent forwarding:** off by default because a privileged user on the remote
  host could use the forwarded agent while the connection is active.
- **X11 forwarding:** off by default; when enabled, SSHShift requests OpenSSH's
  untrusted X11 mode.
- **Equivalent command:** shows the ordinary OpenSSH command represented by the
  selected options.

## Testing

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile ssh-shift
```

The tests cover endpoint validation, configuration-injection defenses, native
UI defaults, command previews, HMAC host aliases, private file permissions,
OpenSSH configuration parsing, and destination-free launcher arguments.

## Threat-model boundaries

SSHShift prevents this launcher and OpenSSH's user known-host file from
retaining recoverable destination names. It cannot hide a live connection from
DNS, network equipment, the destination, the operating system, or an attacker
able to inspect process memory or an unlocked KDE Wallet. See
[SECURITY.md](SECURITY.md) for details.

OpenSSH remains responsible for SSH cryptography, authentication, protocol
compatibility, host-key validation, and the remote session.

## License

MIT. See [LICENSE](LICENSE).
