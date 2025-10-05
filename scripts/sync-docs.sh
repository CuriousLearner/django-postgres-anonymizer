#!/bin/bash
# Sync all documentation files from Markdown to RST
# This script keeps documentation in sync across formats

set -e

echo "🔄 Syncing documentation files..."
echo ""

# README
echo "📄 Converting README.md to README.rst..."
pandoc README.md -f markdown -t rst -o README.rst
echo "   Appending toctree to docs/index.rst..."
cp README.rst docs/index.rst
cat >> docs/index.rst << 'EOF'

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Getting Started

   getting-started/index

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: User Guide

   guides/usage-patterns

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Examples & Use Cases

   examples/django-auth

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Deployment

   deployment/production

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: API Reference

   reference/settings
   reference/api

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
EOF

# CHANGELOG
echo "📝 Syncing CHANGELOG.rst to docs/changelog.rst..."
cp CHANGELOG.rst docs/changelog.rst

# CONTRIBUTING
echo "🤝 Syncing CONTRIBUTING.rst to docs/contributing.rst..."
cp CONTRIBUTING.rst docs/contributing.rst

echo ""
echo "✅ Documentation synced successfully!"
echo ""
echo "Files synced:"
echo "  • README.md → README.rst → docs/index.rst"
echo "  • CHANGELOG.rst → docs/changelog.rst"
echo "  • CONTRIBUTING.rst → docs/contributing.rst"
