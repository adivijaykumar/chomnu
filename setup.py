import os
from setuptools import setup

# Set by the release CI from the git tag; falls back to 0.0.0 for local builds.
version = os.environ.get('RELEASE_VERSION', '0.0.0').lstrip('v')

APP = ['app.py']
DATA_FILES = [
    ('assets', [
        'assets/style.css',
        'assets/mathjax.min.js',
        'assets/mermaid.min.js',
    ]),
]
OPTIONS = {
    'argv_emulation': False,
    'infoplist_file': 'macos/Info.plist',
    'packages': ['webview', 'markdown', 'pymdownx', 'pygments'],
    'includes': [
        'webview.platforms.cocoa',
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.toc',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
        'markdown.extensions.admonition',
        'pymdownx.arithmatex',
    ],
}

setup(
    name='Chomnu',
    version=version,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
