from setuptools import (
    setup,
    find_packages)

from aiolxd import (
    __version__,
    __doc__ as description)


config = {
    'name': 'aiolxd',
    'version': __version__,
    'license': 'LGPLv3+',
    'description': description,
    'long_description': open('README.rst').read(),
    'author': 'Alberto Donato',
    'author_email': 'alberto.donato@gmail.com',
    'maintainer': 'Alberto Donato',
    'maintainer_email': 'alberto.donato@gmail.com',
    'url': 'https://github.com/albertodonato/aiolxd',
    'download_url': 'None',
    'packages': find_packages(),
    'include_package_data': True,
    'entry_points': {'console_scripts': []},
    'test_suite': 'aiolxd',
    'install_requires': ['aiohttp', 'pyxdg', 'PyYAML', 'toolrack'],
    'tests_require': [],
    'keywords': '',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        ('License :: OSI Approved :: '
         'GNU Lesser General Public License v3 or later (LGPLv3+)'),
        'Programming Language :: Python :: 3 :: Only']}

setup(**config)
