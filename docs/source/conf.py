#
# Documentation build configuration file, created by sphinx-quickstart
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.
import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))

bibtex_bibfiles = ["refs.bib"]


# -- General configuration ----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "1.6"

# Add any Sphinx extension module names here, as strings.
# They can be extensions coming with Sphinx (named "sphinx.ext.*")
# or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxcontrib.bibtex",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "nbsphinx",
]

# Mock imports.
autodoc_mock_imports = [
    "estimagic",
    "matplotlib",
    "estimagic",
    "jax",
    "numpy",
    "pandas",
    "scipy",
    "seaborn",
    "statsmodels",
    "filterpy",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
source_encoding = "utf-8"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "skillmodels"
copyright = "2016-2019, Janos Gabler"

# The version info for the project you"re documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "0.1"
# The full version, including alpha/beta/rc tags.
release = "0.1.0dev4"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ""
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%d %B %Y"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, "()" will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = ["src."]


# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "pydata_sphinx_theme"

html_logo = "_static/images/logo.svg"

html_theme_options = {"github_url": "https://github.com/OpenSourceEconomics/estimagic"}

html_css_files = ["css/custom.css"]

html_sidebars = {
    "**": [
        "relations.html",  # needs 'show_related': True theme option to display
        "searchbox.html",
    ]
}

templates_path = ["_templates"]
html_static_path = ["_static"]


html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ""

# This is the file name suffix for HTML files (e.g. ".xhtml").
html_file_suffix = ".html"

# Output file base name for HTML help builder.
htmlhelp_basename = "somedoc"

# Other settings

autodoc_member_order = "bysource"
napoleon_use_rtype = False
napoleon_include_private_with_doc = False
todo_include_todos = True
