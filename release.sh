#!/bin/bash
# Helper script to create a new release
# Usage: ./release.sh 1.2.1

set -e

if [ -z "$1" ]; then
  echo "Usage: ./release.sh <version>"
  echo "Example: ./release.sh 1.2.1"
  exit 1
fi

VERSION="$1"
echo "Creating release v$VERSION..."

# Update manifest.json version
echo "Updating manifest.json..."
sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/cleardarksky/manifest.json
rm custom_components/cleardarksky/manifest.json.bak 2>/dev/null || true

# Check if CHANGELOG.md needs updating
if ! grep -q "## \[$VERSION\]" CHANGELOG.md; then
  echo ""
  echo "⚠️  CHANGELOG.md does not contain version $VERSION"
  echo "Please update CHANGELOG.md before continuing."
  echo ""
  read -p "Open CHANGELOG.md now? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    ${EDITOR:-nano} CHANGELOG.md
  fi
  exit 1
fi

# Show changes
echo ""
echo "Changes to be released:"
git diff custom_components/cleardarksky/manifest.json

echo ""
read -p "Create release v$VERSION? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Release cancelled."
  git checkout custom_components/cleardarksky/manifest.json
  exit 1
fi

# Commit and tag
git add custom_components/cleardarksky/manifest.json CHANGELOG.md
git commit -m "Release v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"

echo ""
echo "✅ Release prepared locally!"
echo ""
echo "Next steps:"
echo "  1. Review the commit: git show HEAD"
echo "  2. Push to GitHub: git push origin main --tags"
echo "  3. GitHub Actions will automatically create the release"
echo ""
echo "Or to cancel:"
echo "  git reset HEAD~1"
echo "  git tag -d v$VERSION"
