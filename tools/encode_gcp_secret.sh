#!/bin/bash
# Helper script to encode GCP credentials for GitHub Secrets

set -e

CREDENTIALS_FILE="${1:-backend/config/credentials.json}"

# Check if file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Error: Credentials file not found: $CREDENTIALS_FILE"
    echo ""
    echo "Usage: bash tools/encode_gcp_secret.sh [path/to/credentials.json]"
    echo "Default: backend/config/credentials.json"
    exit 1
fi

# Verify it's valid JSON
if ! python -m json.tool "$CREDENTIALS_FILE" > /dev/null 2>&1; then
    echo "❌ Error: File is not valid JSON: $CREDENTIALS_FILE"
    exit 1
fi

echo "✅ Found credentials file: $CREDENTIALS_FILE"
echo ""

# Encode to base64
echo "🔐 Encoding to base64..."
BASE64_STRING=$(base64 "$CREDENTIALS_FILE" | tr -d '\n')

echo ""
echo "=========================================="
echo "📋 Base64-Encoded Secret (copy this value)"
echo "=========================================="
echo ""
echo "$BASE64_STRING"
echo ""
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "1. Copy the base64 string above (Ctrl+C to copy)"
echo "2. Go to GitHub: https://github.com/YOUR_USER/YOUR_REPO/settings/secrets/actions"
echo "3. Click 'New repository secret'"
echo "4. Set Name: GCP_SERVICE_ACCOUNT_KEY_BASE64"
echo "5. Set Value: (paste the base64 string)"
echo "6. Click 'Add secret'"
echo ""
echo "ℹ️  For more details, see: docs/GITHUB_SECRETS_SETUP.md"
echo ""
