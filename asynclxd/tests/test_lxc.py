from pathlib import Path

import yaml

import pytest

from ..lxc import (
    cli_config_dir,
    get_remotes,
)


@pytest.fixture
def config_dir(tmpdir):
    config_dir = Path(tmpdir / "config")
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def mock_config_dir(mocker, config_dir):
    mock = mocker.patch("asynclxd.lxc.cli_config_dir")
    mock.return_value = config_dir
    yield mock


@pytest.fixture
def make_config(config_dir):
    def write(config):
        config_file = config_dir / "config.yml"
        config_file.write_text(yaml.dump(config))

    yield write


@pytest.fixture
def server_cert(config_dir):
    servercerts_dir = config_dir / "servercerts"
    servercerts_dir.mkdir()
    cert_file = servercerts_dir / "r.crt"
    cert_file.write_text("server cert")
    yield cert_file


@pytest.fixture
def client_certs(config_dir):
    key_file = config_dir / "client.key"
    key_file.write_text("client key")
    cert_file = config_dir / "client.crt"
    cert_file.write_text("client cert")
    yield key_file, cert_file


@pytest.mark.usefixtures("mock_config_dir")
class TestGetRemotes:
    def test_config_dir_default(self, mock_config_dir):
        """By default, the 'lxc' CLI config dir is used."""
        get_remotes()
        mock_config_dir.assert_called()

    def test_config_dir_not_existent(self, config_dir):
        """If the config dir doesn't exist, an empty dict is returned."""
        config_dir.rmdir()
        assert get_remotes() == {}

    def test_no_config(self, config_dir):
        """An empty dict is returned if no config file is found."""
        assert get_remotes() == {}

    def test_no_remotes(self, config_dir, make_config):
        """An empty dict is returned if no remotes are defined."""
        make_config({"remotes": {}})
        assert get_remotes() == {}

    def test_remotes(self, make_config):
        """LXD remotes are returned."""
        make_config(
            {
                "remotes": {
                    "local": {"addr": "unix:///path/to/socket"},
                    "other": {"addr": "https://example.com:8443", "protocol": "lxd"},
                }
            }
        )
        remotes = get_remotes()
        assert sorted(remotes) == ["local", "other"]
        assert str(remotes["local"].uri) == "unix:///path/to/socket"
        assert str(remotes["other"].uri) == "https://example.com:8443/"

    def test_default_unix_socket_path(self, make_config):
        """If a path is not specified for the socket, the default is used."""
        make_config({"remotes": {"local": {"addr": "unix://"}}})
        remotes = get_remotes()
        assert remotes["local"].uri.path == "/var/lib/lxd/unix.socket"

    def test_ignore_non_lxd(self, make_config):
        """Remotes that don't use the 'lxd' protocol are ignored."""
        make_config(
            {
                "remotes": {
                    "local": {"addr": "unix:///path/to/socket"},
                    "other": {
                        "addr": "https://example.com:8443",
                        "protocol": "simplestreams",
                    },
                }
            }
        )
        remotes = get_remotes()
        assert list(remotes) == ["local"]

    def test_remote_no_certificates(self, make_config):
        """No certificates are loaded for UNIX remotes."""
        make_config({"remotes": {"local": {"addr": "unix://"}}})
        remotes = get_remotes()
        assert remotes["local"].certs is None

    def test_remote_no_certificates_if_no_server_cert(self, config_dir, make_config):
        """No certificates are loaded if no server cert is found."""
        make_config({"remotes": {"r": {"addr": "https://1.2.3.4:8443"}}})
        (config_dir / "client.crt").write_text("client cert")
        (config_dir / "client.key").write_text("client key")
        remotes = get_remotes()
        assert remotes["r"].certs is None

    def test_remote_with_certs_if_server_cert(
        self, config_dir, make_config, server_cert
    ):
        """Remote certificates are set if server certificate is found."""
        make_config({"remotes": {"r": {"addr": "https://1.2.3.4:8443"}}})
        remotes = get_remotes()
        assert remotes["r"].certs.server_cert is not None

    def test_remote_with_certs(
        self, config_dir, make_config, server_cert, client_certs
    ):
        """Remote certificates are set if found."""
        make_config({"remotes": {"r": {"addr": "https://1.2.3.4:8443"}}})
        remotes = get_remotes()
        certs = remotes["r"].certs
        assert certs.server_cert is not None
        assert certs.client_cert is not None
        assert certs.client_key is not None


class TestCLIConfigDir:
    def test_cli_config_dir(self):
        """cli_config_dir returns the directory for the lxc CLI config."""
        config_dir = cli_config_dir()
        assert config_dir.name == "lxc"
