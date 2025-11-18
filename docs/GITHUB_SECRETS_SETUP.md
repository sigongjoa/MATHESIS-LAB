# GitHub Secrets Setup for CI/CD

This guide explains how to properly configure GitHub Secrets for the CI/CD pipeline to work with GCP credentials.

## Why Base64 Encoding?

GitHub Secrets with multi-line content (like JSON) can have issues with:
- Newline character handling
- Special character escaping
- Line ending differences (CRLF vs LF)

**Base64 encoding solves all these issues** by converting the JSON into a single-line string that GitHub Actions can reliably pass through environment variables.

## Setup Steps

### Step 1: Convert credentials.json to Base64

Run this command in your terminal to convert the credentials file:

```bash
# On Linux/macOS:
base64 backend/config/credentials.json | tr -d '\n'

# On Windows (PowerShell):
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes('backend/config/credentials.json'))
```

This will output a single long string of base64-encoded text. **Copy the entire output.**

### Step 2: Add Secret to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Set the following:
   - **Name:** `GCP_SERVICE_ACCOUNT_KEY_BASE64`
   - **Value:** Paste the entire base64-encoded string from Step 1
5. Click **Add secret**

### Step 3: Verify the Secret

The secret is now stored securely. The CI/CD pipeline will:
1. Receive the base64-encoded string
2. Decode it back to JSON
3. Verify it's valid JSON
4. Create the credentials file

## Testing

Once the secret is added, push a commit to trigger the workflow:

```bash
git add .
git commit -m "test: Trigger CI/CD with new GCP secret"
git push
```

Then check the GitHub Actions logs:
- Go to **Actions** tab
- Click the latest workflow run
- Look for "Create GCP credentials file" step
- You should see:
  - ✅ GCP credentials file created successfully
  - ✅ GCP credentials file is valid JSON

## Troubleshooting

### Issue: "GCP_SERVICE_ACCOUNT_KEY_BASE64 secret not set"

**Cause:** The secret name doesn't match or wasn't added correctly.

**Solution:**
1. Check that the secret name is exactly `GCP_SERVICE_ACCOUNT_KEY_BASE64` (case-sensitive)
2. Go to Settings → Secrets and verify it exists
3. If not, add it again following Step 2

### Issue: "GCP credentials file is invalid JSON"

**Cause:** The base64 encoding was corrupted.

**Solution:**
1. Re-run the base64 command from Step 1
2. Make sure you copy the ENTIRE output (it should be a very long string)
3. Update the secret with the new value
4. Push a new commit to test

### Issue: "AttributeError: 'NoneType' object has no attribute 'from_service_account_file'"

**Cause:** The credentials file wasn't created or is invalid.

**Solution:**
1. Check the GitHub Actions logs for the "Create GCP credentials file" step
2. If it shows the ⚠️ message about the secret not being set, you need to add the secret
3. If it shows an error, re-check the base64 encoding

## Important Notes

- **Security:** The base64 string is just encoding, not encryption. GitHub Secrets provide the encryption. Never commit this string to version control.
- **Base64 is reversible:** Anyone with the base64 string can decode it back to JSON. That's why it's stored as a Secret, not in the code.
- **The credentials file is never committed:** It's only created at runtime in the GitHub Actions runner (temporary VM), then deleted after the job completes.

## Quick Reference

**Command to encode:**
```bash
base64 backend/config/credentials.json | tr -d '\n'
```

**Secret Name:**
```
GCP_SERVICE_ACCOUNT_KEY_BASE64
```

**Workflow Usage:**
```yaml
env:
  GCP_KEY_BASE64: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY_BASE64 }}
run: |
  echo "$GCP_KEY_BASE64" | base64 -d > backend/config/credentials.json
```
