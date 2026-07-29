# SSHShift

**Shift from Windows key → PuTTY → Enter → host → Enter to Debian's
OpenSSH—without a hard landing.**

SSHShift is a profile-free KDE launcher for OpenSSH, built for Windows
administrators moving their daily work to Debian. It provides a familiar
“enter a host and connect” window, then gets out of the way and lets the
system's real `ssh` client run inside Konsole.

## The Shift suite

| Tool | Familiar starting point | Debian engine |
| --- | --- | --- |
| [RDPShift](https://github.com/MadsIT-com/rdp-shift) | An `mstsc`-style “enter a computer and connect” workflow | [FreeRDP](https://www.freerdp.com/) |
| [SSHShift](https://github.com/MadsIT-com/ssh-shift) | `Windows key → PuTTY → Enter → host → Enter`, made native to KDE | [OpenSSH](https://www.openssh.com/) + Konsole |
| [MapShift](https://github.com/MadsIT-com/map-shift) | A familiar “map network drive” path into KDE applications | KDE KIO SMB + KIO-FUSE |
| [ServiceShift](https://github.com/MadsIT-com/service-shift) | A `services.msc`-style overview with familiar service controls | systemd + PolicyKit |
| [TaskShift](https://github.com/MadsIT-com/task-shift) | A Task Scheduler-style overview with safe schedule editing | systemd timers + PolicyKit |

SSHShift supports Debian 13 with KDE Plasma and Wayland.

## Why it exists

Debian already ships excellent administration tools, but a command prompt can
be an unnecessarily abrupt first step for administrators arriving from
Windows. SSHShift provides a softer landing without replacing OpenSSH,
inventing a new protocol stack, or locking users into its interface.

The Advanced options panel shows the equivalent `ssh` command for the current
choices. The launcher can therefore act as training wheels: use the graphical
workflow today and take the same command to a terminal whenever you are ready.

## Updates stay with Debian

SSHShift does not bundle its own SSH implementation. It launches the OpenSSH
and Konsole packages maintained by Debian, so normal `apt` upgrades deliver
their security and bug fixes through the same trusted update path as the rest
of the system. There is no separate full client, private protocol copy, or
extra updater that can quietly fall behind.

The small wrapper may occasionally need a compatibility or interface update,
but the security-sensitive SSH engine remains Debian's package—not frozen
inside SSHShift.

## Behavior and privacy

- No connection profiles, recent-host list, saved usernames, or saved
  passwords.
- Destination and optional jump-host details have separate cards on the main
  screen, each pairing its Host and Username fields clearly. Host fields also
  accept `[username@]hostname[:port]` notation.
- Authentication is performed directly by OpenSSH in Konsole. SSHShift never
  asks for or handles the password.
- The hostname, username, jump host, and options are supplied through a private
  OpenSSH configuration under `/run/user/$UID`, not command-line arguments.
- The private runtime directory is removed when the Konsole session ends.
- Persistent host-key lookup uses a keyed HMAC of the normalized hostname and
  port as an opaque identity.
- The random HMAC key is held in KDE Wallet.
- The real hostname exists in a private known-hosts file under `/run/user/$UID`
  only while the session is active, so OpenSSH's prompts remain readable.
- When the session ends, SSHShift translates the transient hostname back to
  its opaque identity before updating persistent trust.
- OpenSSH asks before trusting a host for the first time, silently accepts an
  unchanged key, and refuses a changed key.
- SSH agent and X11 forwarding are off by default and reset after each launch.
- An explicitly selected identity file and jump host apply only to the current
  connection.

The persistent known-host database is stored at
`$XDG_DATA_HOME/ssh-shift/known_hosts`, normally
`~/.local/share/ssh-shift/known_hosts`. It contains public host keys indexed by
KDE-Wallet-keyed opaque aliases—not server names.

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

## Connection options

- **Identity file:** selects one private key for this connection. When empty,
  OpenSSH uses its normal default keys and SSH agent.
- **Jump host:** routes through a bastion using OpenSSH `ProxyJump`; it is on the
  main screen because bastions are part of many administrators' daily workflow.
  A separate Jump username field is provided, while `username@host` notation
  remains supported. Its identity is protected in the same known-host database.
- **Agent forwarding:** off by default because a privileged user on the remote
  host could use the forwarded agent while the connection is active.
- **X11 forwarding:** off by default; when enabled, SSHShift requests OpenSSH's
  untrusted X11 mode.
- **Equivalent command:** shows the ordinary OpenSSH command represented by the
  selected options in the Advanced panel.

If Konsole needs time to start, SSHShift displays a cancellable progress window
instead of appearing unresponsive.

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
