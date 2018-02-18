"""Helpers to access configuration for the LXD CLI (lxc)."""

from pathlib import Path

from xdg.BaseDirectory import xdg_config_home
import yaml

from .remote import (
    Remote,
    SSLCerts,
)


def get_remotes(config_dir=None):
    """Return a list of :class:`Remote`s from the lxc config."""
    if config_dir is None:
        config_dir = cli_config_dir()
    config_file = Path(config_dir) / 'config.yml'
    try:
        with config_file.open() as fd:
            config = yaml.load(fd)
    except FileNotFoundError:
        return {}

    return {
        name: Remote(conf.get('addr'), certs=_get_certs(config_dir, name))
        for name, conf in config.get('remotes', []).items()
        if conf.get('protocol') in ('lxd', None)}


def cli_config_dir():
    """Return the configuration directory for the 'lxc' CLI."""
    return Path(xdg_config_home) / 'lxc'


def _get_certs(config_dir, remote_name):
    """Return SSLCerts for the remote, or None if certs are not found."""
    config_dir = Path(config_dir)
    server_cert = config_dir / 'servercerts/{}.crt'.format(remote_name)
    client_key = config_dir / 'client.key'
    client_cert = config_dir / 'client.crt'

    if not server_cert.exists():
        return None
    return SSLCerts(
        server_cert=server_cert,
        client_cert=client_cert if client_cert.exists() else None,
        client_key=client_key if client_key.exists() else None)
