import os
import sys
sys.path.insert(0, os.path.abspath('../backend'))

# Import-time safety for autodoc: firebase_service raises at import when
# FIREBASE_KEY_PATH is missing unless TEST_MODE is enabled, and database.py
# creates the SQLAlchemy engine from DATABASE_URL as soon as it is imported.
os.environ.setdefault('TEST_MODE', 'true')
os.environ.setdefault('DATABASE_URL', 'sqlite://')

project = 'ClimaNuvem'
copyright = '2026, Fernando Uria Navarro'
author = 'Fernando Uria Navarro'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# firebase_admin requires real credentials on import; it is mocked so autodoc
# can import the app modules without secrets in CI.
autodoc_mock_imports = ['firebase_admin']

# Pre-import the whole app before autodoc processes any module so every
# documented module is resolved from the healthy cached copies in sys.modules.
from sphinx.ext.autodoc.mock import mock
with mock(autodoc_mock_imports):
    import app.main  # noqa: F401  (chain-imports all documented modules)

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
