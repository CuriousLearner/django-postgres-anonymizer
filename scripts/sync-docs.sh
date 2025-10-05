#!/bin/bash
# Sync documentation files
# This script converts README.md to RST and adds toctree for Sphinx

set -e

echo "🔄 Syncing documentation files..."
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ Error: pandoc is not installed"
    echo "   Install with: brew install pandoc (macOS) or apt-get install pandoc (Linux)"
    exit 1
fi

# Convert README.md to RST for docs/index.rst
echo "📄 Converting README.md to docs/index.rst..."
pandoc README.md -f markdown -t rst -o docs/index.rst

# Fix mermaid code blocks for Sphinx
# Pandoc converts ```mermaid to .. code:: mermaid, but we need .. mermaid::
sed -i '' 's/\.\. code:: mermaid/.. mermaid::/g' docs/index.rst

# Append toctree to docs/index.rst
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
   :caption: Reference

   reference/settings
   reference/api

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
EOF

echo ""
echo "✅ Documentation synced successfully!"
echo ""
echo "Files synced:"
echo "  • README.md → docs/index.rst (with toctree appended)"
echo ""
echo "Note:"
echo "  • docs/contributing.rst uses '.. include:: ../CONTRIBUTING.rst'"
echo "  • docs/changelog.rst uses '.. include:: ../CHANGELOG.rst'"
