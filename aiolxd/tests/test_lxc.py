from unittest import mock

from toolrack.testing import (
    TempDirFixture,
    TestCase,
)
import yaml

from ..lxc import (
    get_lxc_remotes,
    lxc_config_dir,
)


class TestGetLXCRemotes(TestCase):

    def setUp(self):
        super().setUp()
        self.tempdir = self.useFixture(TempDirFixture())

    def make_config(self, config):
        return self.tempdir.mkfile(
            path='config.yml', content=yaml.dump(config))

    @mock.patch('aiolxd.lxc.lxc_config_dir')
    def test_config_dir_default(self, mock_config_dir):
        """By default, the 'lxc' CLI config dir is used."""
        mock_config_dir.return_value = '/some/dir'
        get_lxc_remotes()
        mock_config_dir.assert_called()

    def test_config_dir_not_existent(self):
        """If the config dir doesn't exist, an empty dict is returned."""
        self.assertEqual({}, get_lxc_remotes(config_dir='/'))

    def test_no_config(self):
        """An empty dict is returned if no config file is found."""
        self.assertEqual(get_lxc_remotes(config_dir='/not/here'), {})

    def test_no_remotes(self):
        self.make_config({'remotes': {}})
        self.assertEqual(get_lxc_remotes(config_dir=self.tempdir.path), {})

    def test_remotes(self):
        """LXD remotes are returned."""
        self.make_config(
            {'remotes': {
                'local': {
                    'addr': 'unix:///path/to/socket'},
                'other': {
                    'addr': 'https://example.com:8443',
                    'protocol': 'lxd'}}})
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertCountEqual(remotes, ['local', 'other'])
        self.assertEqual(
            str(remotes['local'].uri), 'unix:///path/to/socket')
        self.assertEqual(
            str(remotes['other'].uri), 'https://example.com:8443/')

    def test_default_unix_socket_path(self):
        """If a path is not specified for the socket, the default is used."""
        self.make_config({'remotes': {'local': {'addr': 'unix://'}}})
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertEqual(remotes['local'].uri.path, '/var/lib/lxd/unix.socket')

    def test_ignore_non_lxd(self):
        """Remotes that don't use the 'lxd' protocol are ignored."""
        self.make_config(
            {'remotes': {
                'local': {
                    'addr': 'unix:///path/to/socket'},
                'other': {
                    'addr': 'https://example.com:8443',
                    'protocol': 'simplestreams'}}})
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertCountEqual(remotes, ['local'])

    def test_remote_no_certificates(self):
        """No certificates are loaded for UNIX remotes."""
        self.make_config({'remotes': {'local': {'addr': 'unix://'}}})
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertIsNone(remotes['local'].certs)

    def test_remote_no_certificates_if_no_server_cert(self):
        """No certificates are loaded if no server cert is found."""
        self.make_config({'remotes': {'r': {'addr': 'https://1.2.3.4:8443'}}})
        self.tempdir.mkfile(path='client.crt', content='client cert')
        self.tempdir.mkfile(path='client.key', content='client key')
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertIsNone(remotes['r'].certs)

    def test_remote_with_certs_if_server_cert(self):
        """Remote certificates are set if server certificate is found."""
        self.make_config({'remotes': {'r': {'addr': 'https://1.2.3.4:8443'}}})
        self.tempdir.mkfile(path='servercerts/r.crt', content='server cert')
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        self.assertIsNotNone(remotes['r'].certs.server_cert)

    def test_remote_with_certs(self):
        """Remote certificates are set if found."""
        self.make_config({'remotes': {'r': {'addr': 'https://1.2.3.4:8443'}}})
        self.tempdir.mkfile(path='servercerts/r.crt', content='server cert')
        self.tempdir.mkfile(path='client.crt', content='client cert')
        self.tempdir.mkfile(path='client.key', content='client key')
        remotes = get_lxc_remotes(config_dir=self.tempdir.path)
        certs = remotes['r'].certs
        self.assertIsNotNone(certs.server_cert)
        self.assertIsNotNone(certs.client_cert)
        self.assertIsNotNone(certs.client_key)


class TestLXCConfigDir(TestCase):

    def test_lxc_config_dir(self):
        """lxc_config_dir returns the directory for the lxc CLI config."""
        config_dir = lxc_config_dir()
        self.assertEqual(config_dir.name, 'lxc')
