# Release Process

This document explains how to create new releases for the ClearDarkSky integration.

## Automated Release System

This project uses **GitHub Actions** to automatically create releases when you push a version tag. This ensures HACS compatibility and consistent releases.

## How to Create a Release

### Method 1: Using the Helper Script (Recommended)

#### On Windows (PowerShell):
```powershell
.\release.ps1 1.2.1
```

#### On Linux/Mac/WSL (Bash):
```bash
chmod +x release.sh
./release.sh 1.2.1
```

The script will:
1. ✅ Update `manifest.json` with the new version
2. ✅ Verify `CHANGELOG.md` has an entry for this version
3. ✅ Create a commit with the version changes
4. ✅ Create a git tag (e.g., `v1.2.1`)
5. ✅ Show you what to do next

**After running the script:**
```bash
# Review the changes
git show HEAD

# Push to GitHub (this triggers the automated release)
git push origin main --tags
```

GitHub Actions will automatically:
- ✅ Verify version matches between tag and manifest.json
- ✅ Extract the changelog for this version
- ✅ Create a GitHub Release with proper notes
- ✅ HACS will detect the new release within ~30 minutes

---

### Method 2: Manual Process

If you prefer to do it manually:

#### Step 1: Update CHANGELOG.md
Add a new section for your version:
```markdown
## [1.2.1] - 2025-12-06

### Fixed
- Bug fix description here

### Added
- New feature description here
```

#### Step 2: Update manifest.json
```json
{
  "version": "1.2.1"
}
```

#### Step 3: Commit and Tag
```bash
git add CHANGELOG.md custom_components/cleardarksky/manifest.json
git commit -m "Release v1.2.1"
git tag -a v1.2.1 -m "Release v1.2.1"
git push origin main --tags
```

#### Step 4: Wait for GitHub Actions
- Go to your GitHub repository → Actions tab
- Watch the "Release" workflow complete
- A new release will appear under Releases

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x) - Breaking changes, incompatible API changes
- **MINOR** (x.2.x) - New features, backwards compatible
- **PATCH** (x.x.1) - Bug fixes, backwards compatible

Examples:
- `1.0.0` → `1.0.1` - Bug fix
- `1.0.1` → `1.1.0` - New feature (like improved color mapping)
- `1.1.0` → `2.0.0` - Breaking change (like removing a sensor)

---

## Testing a Release

### Before Pushing Tags

1. **Test locally first:**
   ```bash
   # Make your changes
   # Test thoroughly in Home Assistant
   ```

2. **Update CHANGELOG.md** with all changes

3. **Run the release script** (it won't push automatically)

4. **Review the commit:**
   ```bash
   git show HEAD
   ```

5. **If satisfied, push:**
   ```bash
   git push origin main --tags
   ```

### Testing the GitHub Action

To test the workflow without creating a real release:

1. Create a test tag:
   ```bash
   git tag v0.0.1-test
   git push origin v0.0.1-test
   ```

2. Watch the Actions tab on GitHub

3. Delete the test release and tag when done:
   ```bash
   # On GitHub: Delete the release manually
   git tag -d v0.0.1-test
   git push origin :refs/tags/v0.0.1-test
   ```

---

## Troubleshooting

### "Version mismatch" error in GitHub Actions

The workflow checks that your git tag matches `manifest.json`. If you see this error:

1. Check your tag: `git tag -l`
2. Check manifest.json: `grep version custom_components/cleardarksky/manifest.json`
3. They must match exactly (e.g., tag `v1.2.0` requires manifest `"version": "1.2.0"`)

Fix:
```bash
# Delete the wrong tag
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Fix manifest.json
# Then create the tag again
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags
```

### Changelog not showing in release

Make sure your `CHANGELOG.md` has this exact format:
```markdown
## [1.2.0] - 2025-12-06

Your changes here...

## [1.1.0] - 2024-11-01
```

The version must be in square brackets and match your tag.

### HACS not detecting the new release

- HACS checks for updates every ~30 minutes to a few hours
- Force a refresh: HACS → Integrations → ⋮ → Recheck
- Ensure your tag follows semver: `v1.2.0` not `1.2.0` or `version-1.2.0`

---

## Release Checklist

Use this checklist for every release:

- [ ] All changes tested in Home Assistant
- [ ] CHANGELOG.md updated with new version section
- [ ] manifest.json version updated
- [ ] Run release script or manual commands
- [ ] Review git commit and tag
- [ ] Push to GitHub: `git push origin main --tags`
- [ ] Verify GitHub Action completes successfully
- [ ] Check that release appears on GitHub
- [ ] Wait 30 min and verify HACS detects the update
- [ ] Test installation via HACS on a clean instance (optional)

---

## Example Release Flow

Here's a complete example of releasing v1.3.0:

```bash
# 1. Make your code changes
# ... edit files ...

# 2. Update CHANGELOG.md
# Add section for [1.3.0]

# 3. Run release script
.\release.ps1 1.3.0

# Script will update manifest.json and create commit + tag

# 4. Review
git show HEAD

# 5. Push
git push origin main --tags

# 6. GitHub Actions automatically creates the release
# 7. HACS detects it within 30 minutes
# 8. Users can update!
```

---

## Questions?

If you have questions about the release process, check:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [HACS Integration Documentation](https://hacs.xyz/docs/publish/integration)
