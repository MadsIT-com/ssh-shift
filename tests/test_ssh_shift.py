from __future__ import annotations

import gc
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PROJECT_DIR = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader(
    "ssh_shift", str(PROJECT_DIR / "ssh-shift")
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
ssh_shift = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ssh_shift
LOADER.exec_module(ssh_shift)


class EndpointParsingTests(unittest.TestCase):
    def test_hostname_and_default_port(self) -> None:
        self.assertEqual(
            ssh_shift.parse_endpoint("Server.Example."),
            ssh_shift.Endpoint("server.example", 22),
        )

    def test_hostname_and_custom_port(self) -> None:
        self.assertEqual(
            ssh_shift.parse_endpoint("server:2222"),
            ssh_shift.Endpoint("server", 2222),
        )

    def test_ipv4_and_ipv6_are_canonicalized(self) -> None:
        self.assertEqual(
            ssh_shift.parse_endpoint("192.0.2.10"),
            ssh_shift.Endpoint("192.0.2.10", 22),
        )
        self.assertEqual(
            ssh_shift.parse_endpoint("[2001:0db8::1]:2222"),
            ssh_shift.Endpoint("2001:db8::1", 2222),
        )

    def test_invalid_endpoints_are_rejected(self) -> None:
        values = ("", "bad host", "host:0", "host:65536", "[not-ipv6]", "host/option")
        for value in values:
            with self.subTest(value=value), self.assertRaises(ssh_shift.SSHShiftError):
                ssh_shift.parse_endpoint(value)

    def test_username_validation_blocks_config_injection(self) -> None:
        self.assertEqual(ssh_shift.validate_username("admin@example"), "admin@example")
        for value in ("bad user", "admin\nProxyCommand evil", 'admin"'):
            with self.subTest(value=value), self.assertRaises(ssh_shift.SSHShiftError):
                ssh_shift.validate_username(value)

    def test_username_at_host_destination(self) -> None:
        endpoint, username = ssh_shift.parse_destination("alice@server.example:2222")
        self.assertEqual(endpoint, ssh_shift.Endpoint("server.example", 2222))
        self.assertEqual(username, "alice")

    def test_username_at_bracketed_ipv6_destination(self) -> None:
        endpoint, username = ssh_shift.parse_destination(
            "admin@example@[2001:0db8::1]:2222"
        )
        self.assertEqual(endpoint, ssh_shift.Endpoint("2001:db8::1", 2222))
        self.assertEqual(username, "admin@example")


class UserInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = ssh_shift.qt_application()

    def test_dialog_has_familiar_fields_and_safe_defaults(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        def labels(form: ssh_shift.QFormLayout) -> list[str]:
            result = []
            for row in range(form.rowCount()):
                item = form.itemAt(row, ssh_shift.QFormLayout.ItemRole.LabelRole)
                self.assertIsNotNone(item)
                result.append(item.widget().text().replace("&", ""))
            return result

        self.assertEqual(dialog.destination_group.title(), "Destination")
        self.assertEqual(labels(dialog.destination_form), ["Host:", "Username:"])
        self.assertEqual(dialog.jump_group.title(), "Jump host (optional)")
        self.assertEqual(labels(dialog.jump_form), ["Host:", "Username:"])
        self.assertGreaterEqual(dialog.width(), 600)
        margins = dialog.main_layout.contentsMargins()
        self.assertEqual(
            (margins.left(), margins.top(), margins.right(), margins.bottom()),
            (20, 18, 20, 16),
        )
        for form in (dialog.destination_form, dialog.jump_form):
            self.assertEqual(form.horizontalSpacing(), 12)
            self.assertEqual(form.verticalSpacing(), 10)
        self.assertTrue(dialog.advanced_panel.isHidden())
        self.assertFalse(dialog.forward_agent.isChecked())
        self.assertFalse(dialog.forward_x11.isChecked())
        dialog.close()

    def test_advanced_options_and_command_preview(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        dialog.host.setText("server.example:2222")
        dialog.username.setText("alice")
        dialog.jump_host.setText("operator@jump.example")
        dialog.forward_agent.setChecked(True)
        dialog.advanced_button.setChecked(True)
        self.assertFalse(dialog.advanced_panel.isHidden())
        self.assertEqual(
            dialog.command_preview.text(),
            "ssh -p 2222 -J operator@jump.example -A alice@server.example",
        )
        request = dialog.values()
        self.assertEqual(request.endpoint, ssh_shift.Endpoint("server.example", 2222))
        self.assertEqual(request.options.jump, ssh_shift.Endpoint("jump.example", 22))
        self.assertEqual(request.options.jump_username, "operator")
        dialog.close()

    def test_separate_jump_username_populates_request(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        dialog.host.setText("server.example")
        dialog.jump_host.setText("jump.example")
        dialog.jump_username.setText("operator")
        request = dialog.values()
        self.assertEqual(request.options.jump, ssh_shift.Endpoint("jump.example", 22))
        self.assertEqual(request.options.jump_username, "operator")
        self.assertEqual(
            dialog.command_preview.text(),
            "ssh -J operator@jump.example server.example",
        )
        dialog.close()

    def test_conflicting_jump_usernames_are_rejected(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        dialog.host.setText("server.example")
        dialog.jump_host.setText("operator@jump.example")
        dialog.jump_username.setText("admin")
        with self.assertRaises(ssh_shift.SSHShiftError):
            dialog.values()
        dialog.close()

    def test_embedded_username_populates_request(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        dialog.host.setText("alice@server.example")
        request = dialog.values()
        self.assertEqual(request.endpoint, ssh_shift.Endpoint("server.example", 22))
        self.assertEqual(request.options.username, "alice")
        self.assertEqual(dialog.command_preview.text(), "ssh alice@server.example")
        dialog.close()

    def test_conflicting_usernames_are_rejected(self) -> None:
        dialog = ssh_shift.ConnectionDialog()
        dialog.host.setText("alice@server.example")
        dialog.username.setText("bob")
        with self.assertRaises(ssh_shift.SSHShiftError):
            dialog.values()
        dialog.close()

    def test_application_survives_a_discarded_caller_reference(self) -> None:
        ssh_shift.qt_application()
        gc.collect()
        dialog = ssh_shift.ConnectionDialog()
        self.assertIsNotNone(ssh_shift.QApplication.instance())
        dialog.close()


class PrivacyConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.environment = mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self.temporary.name}
        )
        self.environment.start()
        self.key = bytes(range(32))
        self.target = ssh_shift.Endpoint("private-server.example", 2222)
        self.jump = ssh_shift.Endpoint("private-jump.example", 22)
        self.request = ssh_shift.ConnectionRequest(
            self.target,
            ssh_shift.ConnectionOptions(
                username="alice",
                identity_file="/home/alice/.ssh/id_ed25519",
                jump=self.jump,
                jump_username="operator",
            ),
        )
        key_path = Path(self.temporary.name) / "test_host_key"
        subprocess.run(
            [
                ssh_shift.SSH_KEYGEN,
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(key_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        public_fields = key_path.with_suffix(".pub").read_text(
            encoding="ascii"
        ).split()
        self.host_key = " ".join(public_fields[:2])

    def tearDown(self) -> None:
        self.environment.stop()
        self.temporary.cleanup()

    def test_host_alias_is_keyed_stable_and_opaque(self) -> None:
        alias = ssh_shift.opaque_host_alias(self.key, self.target)
        self.assertEqual(alias, ssh_shift.opaque_host_alias(self.key, self.target))
        self.assertNotIn(self.target.host, alias)
        self.assertNotEqual(
            alias,
            ssh_shift.opaque_host_alias(bytes(reversed(self.key)), self.target),
        )

    def test_known_hosts_file_is_private(self) -> None:
        known_hosts = ssh_shift.known_hosts_path()
        self.assertEqual(known_hosts.stat().st_mode & 0o777, 0o600)
        self.assertEqual(known_hosts.parent.stat().st_mode & 0o777, 0o700)

    def test_runtime_config_uses_transient_known_hosts_and_safe_defaults(self) -> None:
        known_hosts = Path(self.temporary.name) / "runtime_known_hosts"
        config = ssh_shift.build_ssh_config(self.request, known_hosts)
        self.assertNotIn("HostKeyAlias", config)
        self.assertIn("StrictHostKeyChecking ask", config)
        self.assertIn("HashKnownHosts no", config)
        self.assertIn("ForwardAgent no", config)
        self.assertIn("ForwardX11 no", config)
        self.assertIn("ProxyJump ssh-shift-jump", config)
        self.assertNotIn("ProxyCommand", config)

    def test_openssh_accepts_generated_configuration(self) -> None:
        known_hosts = Path(self.temporary.name) / "runtime_known_hosts"
        known_hosts.touch(mode=0o600)
        config_text = ssh_shift.build_ssh_config(self.request, known_hosts)
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            config.write_text(config_text, encoding="utf-8")
            result = subprocess.run(
                [ssh_shift.SSH, "-G", "-F", str(config), ssh_shift.TARGET_ALIAS],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hostname private-server.example", result.stdout)
        self.assertIn("port 2222", result.stdout)
        self.assertIn("proxyjump ssh-shift-jump", result.stdout)

    def test_legacy_hashed_alias_is_transiently_revealed_and_saved_opaque(self) -> None:
        persistent = ssh_shift.known_hosts_path()
        alias = ssh_shift.opaque_host_alias(self.key, self.target)
        persistent.write_text(f"{alias} {self.host_key}\n", encoding="utf-8")
        subprocess.run(
            [ssh_shift.SSH_KEYGEN, "-H", "-f", str(persistent)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        persistent.with_name(persistent.name + ".old").unlink(missing_ok=True)
        self.assertNotIn(alias, persistent.read_text(encoding="utf-8"))

        runtime_directory = ssh_shift.private_runtime_directory()
        try:
            runtime, mappings = ssh_shift.prepare_session_known_hosts(
                ssh_shift.ConnectionRequest(self.target, ssh_shift.ConnectionOptions()),
                self.key,
                runtime_directory,
            )
            transient = runtime.read_text(encoding="utf-8")
            self.assertIn(ssh_shift.known_hosts_token(self.target), transient)
            self.assertNotIn(alias, transient)

            ssh_shift.persist_session_known_hosts(runtime, mappings)
            saved = persistent.read_text(encoding="utf-8")
            self.assertIn(alias, saved)
            self.assertNotIn(self.target.host, saved)
            self.assertEqual(persistent.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                ssh_shift.known_hosts_lock_path().stat().st_mode & 0o777,
                0o600,
            )
        finally:
            import shutil

            shutil.rmtree(runtime_directory, ignore_errors=True)

    @mock.patch.object(ssh_shift.subprocess, "Popen")
    def test_konsole_arguments_do_not_contain_destinations(self, popen: mock.Mock) -> None:
        process = mock.Mock()
        popen.return_value = process
        directory = ssh_shift.private_runtime_directory()
        try:
            config = ssh_shift.write_runtime_config(directory, "Host test\n")
            self.assertIs(ssh_shift.start_session(config), process)
            arguments = popen.call_args.args[0]
            joined = " ".join(str(argument) for argument in arguments)
            self.assertNotIn(self.target.host, joined)
            self.assertNotIn(self.jump.host, joined)
            self.assertIn(ssh_shift.SSH, arguments)
            self.assertIn(ssh_shift.TARGET_ALIAS, arguments)
        finally:
            import shutil

            shutil.rmtree(directory, ignore_errors=True)


class RuntimeTests(unittest.TestCase):
    def test_private_runtime_config_permissions(self) -> None:
        directory = ssh_shift.private_runtime_directory()
        try:
            config = ssh_shift.write_runtime_config(directory, "Host test\n")
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(ssh_shift.validate_internal_config(str(config)), config)
        finally:
            import shutil

            shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
