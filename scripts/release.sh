#!/bin/bash
# Release script for code-review package
# Publishes to PyPI and optionally TestPyPI
#
# Usage:
#   ./scripts/release.sh          # interactive, asks for confirmation
#   ./scripts/release.sh --test  # upload to TestPyPI only
#   ./scripts/release.sh --dry    # dry run (build only, no upload)
#   ./scripts/release.sh --skip-test  # skip TestPyPI, go straight to PyPI
#
# Credentials (one-time setup):
#   Add to ~/.pypirc:
#
#   [distutils]
#   index-servers = pypi testpypi
#
#   [pypi]
#   username = __token__
#   password = <your PyPI token>
#
#   [testpypi]
#   repository = https://test.pypi.org/legacy/
#   username = __token__
#   password = <your TestPyPI token>
#
# Or set env vars (for CI/CD):
#   export PYPI_TOKEN="pypi-..."
#   export TEST_PYPI_TOKEN="t.pypi..."

set -e

# ── Colours ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Parse args ──────────────────────────────────────────────────
MODE="interactive"  # interactive | test | dry | skip-test
while [[ $# -gt 0 ]]; do
    case "$1" in
        --test)       MODE="test" ;;
        --dry)        MODE="dry" ;;
        --skip-test)  MODE="skip-test" ;;
        --help|-h)
            echo "Usage: $0 [--test|--dry|--skip-test|--help]"
            echo "  --test      Upload to TestPyPI only"
            echo "  --dry       Build only, no upload"
            echo "  --skip-test Skip TestPyPI, go straight to PyPI"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# ── Helpers ─────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }

# ── Check tools ─────────────────────────────────────────────────
info "Checking required tools..."
for tool in python3 twine; do
    if ! command -v $tool &>/dev/null; then
        error "$tool is not installed"
    fi
done
success "All required tools present"

# ── Ensure build tools ───────────────────────────────────────────
info "Installing / upgrading build tools..."
python3 -m pip install --upgrade build twine wheel 2>&1 | tail -3

# ── Version ─────────────────────────────────────────────────────
cd "$(dirname "$0")/.."
VERSION=$(python3 -c "
import sys
ver = sys.version_info
if ver >= (3, 11):
    import tomllib
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
else:
    import tomli
    with open('pyproject.toml', 'rb') as f:
        data = tomli.load(f)
print(data['project']['version'])
" 2>/dev/null)
info "Current version: ${VERSION}"

if [ "$MODE" = "interactive" ]; then
    echo -n "Enter new version (leave blank to keep ${VERSION}): "
    read -r NEW_VERSION
    if [ -n "$NEW_VERSION" ]; then
        VERSION="$NEW_VERSION"
        info "Bumping version to ${VERSION}..."
        # Update pyproject.toml — use sed to avoid any toml library dependency
        sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
        success "Version updated to ${VERSION}"
    fi
elif [ "$MODE" != "dry" ]; then
    # Auto-bump patch version for --test / --skip-test
    MAJOR=$(echo "$VERSION" | cut -d. -f1)
    MINOR=$(echo "$VERSION" | cut -d. -f2)
    PATCH=$(echo "$VERSION" | cut -d. -f3)
    PATCH=$((PATCH + 1))
    NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
    info "Bumping version to ${NEW_VERSION} for upload..."
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
    VERSION="$NEW_VERSION"
fi

# ── Check for uncommitted changes ───────────────────────────────
if [ -d .git ]; then
    if [ -n "$(git status --porcelain)" ]; then
        warn "You have uncommitted changes:"
        git status --short
        if [ "$MODE" = "interactive" ]; then
            echo -n "Continue anyway? [y/N] "
            read -r confirm
            if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
                error "Aborted."
            fi
        fi
    fi
fi

# ── Build ────────────────────────────────────────────────────────
info "Building package..."
rm -rf dist/ build/ *.egg-info
python3 -m build
success "Package built successfully:"
ls -lh dist/

# ── Dry run ─────────────────────────────────────────────────────
if [ "$MODE" = "dry" ]; then
    info "Dry run — no upload performed."
    info "Built files:"
    ls -lh dist/
    exit 0
fi

# ── TestPyPI ────────────────────────────────────────────────────
if [ "$MODE" = "interactive" ] || [ "$MODE" = "test" ] || [ "$MODE" = "skip-test" ]; then
    if [ "$MODE" = "skip-test" ]; then
        info "Skipping TestPyPI upload (--skip-test)"
    else
        info "Uploading to TestPyPI..."
        twine upload \
            --repository testpypi \
            --username 664141154@qq.com \
            --password Zhang!@#123qwe \
            dist/* \
            2>&1 | tail -10
        if [ $? -eq 0 ]; then
            success "Uploaded to TestPyPI: https://test.pypi.org/project/code-review/"
        else
            error "TestPyPI upload failed"
        fi
    fi
fi

# ── PyPI ────────────────────────────────────────────────────────
if [ "$MODE" = "test" ]; then
    info "Test mode — skipping PyPI upload"
else
    info "Uploading to PyPI..."
    twine upload \
        --username 664141154@qq.com \
        --password Zhang!@#123qwe \
        dist/* \
        2>&1 | tail -10
    if [ $? -eq 0 ]; then
        success "Uploaded to PyPI: https://pypi.org/project/code-review/${VERSION}/"
    else
        error "PyPI upload failed"
    fi
fi

echo ""
success "Release complete!"
