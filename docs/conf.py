# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from pathlib import Path

import django

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

project = "Django PostgreSQL Anonymizer"
copyright_text = "2025, Sanyam Khurana"
author = "Sanyam Khurana"
release = "0.2.0-beta.1"
version = "0.2.0"

# Sphinx expects 'copyright' variable
copyright = copyright_text  # noqa: A001

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "myst_parser",  # Support for Markdown files
]

# MyST Parser configuration
myst_enable_extensions = [
    "colon_fence",  # ::: fence blocks
    "deflist",  # Definition lists
    "html_image",  # HTML images
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

# Sphinx Book Theme options - clean, professional design
html_theme_options = {
    "repository_url": "https://github.com/CuriousLearner/django-postgres-anonymizer",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": False,
    "use_download_button": False,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
}

# Use the new Sphinx canonical URL option
html_baseurl = "https://django-postgres-anonymizer.readthedocs.io/"

# Theme-specific settings
html_title = "Django PostgreSQL Anonymizer"
html_logo = None

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "django": ("https://docs.djangoproject.com/en/stable/", "https://docs.djangoproject.com/en/stable/_objects/"),
    "psycopg2": ("https://www.psycopg.org/docs/", None),
}

# Todo extension
todo_include_todos = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_css_files = []  # noqa: ERA001

# Additional options
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Output file base name for HTML help builder.
htmlhelp_basename = "DjangoPostgreSQLAnonymizerdoc"

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    "papersize": "letterpaper",
    # The font size ('10pt', '11pt' or '12pt').
    "pointsize": "10pt",
    # Additional stuff for the LaTeX preamble.
    "preamble": "",
    # Latex figure (float) alignment
    "figure_align": "htbp",
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        "index",
        "DjangoPostgreSQLAnonymizer.tex",
        "Django PostgreSQL Anonymizer Documentation",
        "Sanyam Khurana",
        "manual",
    ),
]

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "django-postgres-anonymizer", "Django PostgreSQL Anonymizer Documentation", [author], 1)]

# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "DjangoPostgreSQLAnonymizer",
        "Django PostgreSQL Anonymizer Documentation",
        author,
        "DjangoPostgreSQLAnonymizer",
        "Django integration for PostgreSQL Anonymizer extension.",
        "Miscellaneous",
    ),
]
