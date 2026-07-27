# Contributing

SSHShift is intentionally small. Focused bug reports, compatibility results,
security reviews, accessibility improvements, and restrained features are
welcome.

Before submitting a change:

1. Run `python3 -m unittest discover -s tests -v`.
2. Run `python3 -m py_compile ssh-shift`.
3. Run `shellcheck install.sh uninstall.sh` when ShellCheck is available.
4. Confirm no hostname, username, private key, credential, or test secret has
   entered the repository.
5. Keep options session-only and keep forwarding disabled by default.

OpenSSH must remain the implementation of SSH. New protocol, authentication,
or cryptographic code is outside the project's scope.
