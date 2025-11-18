# CI/CD Setup Checklist

## Current Status

✅ **Code changes deployed** (commit: 46fadf9)
- GitHub Actions workflow updated to use base64-encoded secrets
- Helper script created to encode credentials
- Complete documentation added

## What You Need To Do

### Step 1: Encode Your GCP Credentials

Run this command in your terminal from the project root:

```bash
bash tools/encode_gcp_secret.sh
```

This will:
1. Find your `backend/config/credentials.json` file
2. Verify it's valid JSON
3. Encode it to base64
4. Display the base64 string

**Output:** You'll see a long base64 string. Copy the ENTIRE string (it will be several hundred characters long).

### Step 2: Add GitHub Secret

1. Go to your GitHub repository: https://github.com/sigongjoa/MATHESIS-LAB
2. Click **Settings** (in the top navigation)
3. Click **Secrets and variables** → **Actions** (on the left sidebar)
4. Click **New repository secret** button
5. Fill in:
   - **Name:** `GCP_SERVICE_ACCOUNT_KEY_BASE64` (exact spelling, case-sensitive)
   - **Value:** Paste the base64 string from Step 1
6. Click **Add secret**

### Step 3: Trigger the CI/CD Pipeline

The pipeline will automatically run when you push:

```bash
git add .
git commit -m "test: Trigger CI/CD with GCP secret"
git push
```

Or, if you just want to test without committing anything, you can use the "Run workflow" button on GitHub Actions.

### Step 4: Check the Results

1. Go to your GitHub repository
2. Click **Actions** tab
3. Look for the latest workflow run (should be "test: Trigger CI/CD..." or similar)
4. Click to view the full run
5. Look for the **"Create GCP credentials file"** step in each job
6. You should see:
   - ✅ GCP credentials file created successfully
   - ✅ GCP credentials file is valid JSON

If you see these messages, the setup is **WORKING**. If you see ⚠️ messages, see Troubleshooting below.

## What Happens in CI/CD

The workflow will:
1. Install dependencies (Python + Node.js)
2. **Create GCP credentials file** from base64 secret ← This is the critical step
3. Run **backend tests** (pytest) - should pass 196+ tests
4. Run **frontend tests** (vitest) - should pass 29+ tests
5. Run **E2E tests** (Playwright) - tests full application flow
6. Generate **test report** with screenshots and metrics

## Troubleshooting

### Problem: "⚠️ GCP_SERVICE_ACCOUNT_KEY_BASE64 secret not set"

**Cause:** The secret name doesn't match exactly.

**Solution:**
1. Double-check the GitHub Secrets page - verify the secret exists
2. Verify the name is exactly: `GCP_SERVICE_ACCOUNT_KEY_BASE64` (case-sensitive)
3. If it doesn't exist, create it following Step 2 above
4. Push a new commit to test

### Problem: "❌ GCP credentials file is invalid JSON"

**Cause:** The base64 encoding was corrupted (maybe incomplete copy-paste).

**Solution:**
1. Run `bash tools/encode_gcp_secret.sh` again
2. Make absolutely sure you copy the ENTIRE output (from start to finish)
3. Go to GitHub Secrets and update the existing secret with the new value
4. Push a new commit to test

### Problem: "❌ Failed to create GCP credentials file"

**Cause:** The secret was set but the decode step failed.

**Solution:**
1. Check that the base64 string in the secret doesn't have extra spaces or line breaks
2. Try deleting and re-creating the secret with the latest encoding
3. Make sure you're using the new workflow (commit 46fadf9 or later)

### Problem: Tests still failing after credentials file is created

**Cause:** The credentials file exists but the tests are still having issues.

**Solution:**
1. Check the specific test error messages in the GitHub Actions logs
2. Look for errors about GoogleDriveService or credentials validation
3. Verify the base64-decoded credentials file contains valid GCP service account credentials
4. If needed, create a fresh `credentials.json` from GCP and re-encode it

## Local Testing (Optional)

Before pushing to GitHub, you can test locally:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Verify credentials file exists
ls -la backend/config/credentials.json

# 3. Run tests locally
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/ -v

# All tests should pass (196 passed at last check)
```

## Files Changed

- ✅ `.github/workflows/test-and-report.yml` - Updated all 3 jobs to use base64 secrets
- ✅ `tools/encode_gcp_secret.sh` - Helper script to encode credentials
- ✅ `docs/GITHUB_SECRETS_SETUP.md` - Detailed documentation

## Questions?

If you get stuck:
1. Check the detailed documentation: `docs/GITHUB_SECRETS_SETUP.md`
2. Look at the GitHub Actions logs for specific error messages
3. Make sure you're using the latest commit (46fadf9 or later)
4. Verify the base64 string is complete and correct

---

**Summary:** Once you follow the 3 simple steps above, your CI/CD pipeline will have proper GCP credentials and all tests should pass automatically on every push!
