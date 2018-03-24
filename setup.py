from pathlib import Path
from setuptools import (
    find_packages,
    setup,
)

from aiolxd import (
    __doc__ as description,
    __version__,
)


tests_require = ['asynctest']

config = {
    'name': 'aiolxd',
    'version': __version__,
    'license': 'LGPLv3+',
    'description': description,
    'long_description': Path('README.rst').read_text(),
    'author': 'Alberto Donato',
    'author_email': 'alberto.donato@gmail.com',
    'maintainer': 'Alberto Donato',
    'maintainer_email': 'alberto.donato@gmail.com',
    'url': 'https://github.com/albertodonato/aiolxd',
    'packages': find_packages(),
    'include_package_data': True,
    'entry_points': {'console_scripts': []},
    'test_suite': 'aiolxd',
    'install_requires': ['aiohttp < 3.1.0', 'pyxdg', 'PyYAML', 'toolrack'],
    'tests_require': tests_require,
    'extras_require': {'testing': tests_require},
    'keywords': 'LXD rest API',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        ('License :: OSI Approved :: '
         'GNU Lesser General Public License v3 or later (LGPLv3+)'),
        'Programming Language :: Python :: 3 :: Only']}

setup(**config)
