#!/bin/bash

# E2E Tests with Screenshot Capture Script
# This script runs Playwright tests and automatically captures screenshots

echo "🚀 Starting E2E Tests with Screenshot Capture..."
echo ""

# Create screenshots directory
mkdir -p e2e-screenshots

# Run Playwright tests
echo "📸 Running Playwright tests with screenshot capture..."
npx playwright test e2e/ \
  --reporter=json \
  --reporter=list \
  2>&1

# Check if tests were run
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ E2E Tests completed successfully"
else
  echo ""
  echo "⚠️  E2E Tests completed with warnings or failures"
fi

# Count screenshots
SCREENSHOT_COUNT=$(ls -1 e2e-screenshots/*.png 2>/dev/null | wc -l)
echo ""
echo "📊 Screenshot Summary:"
echo "   Total screenshots: $SCREENSHOT_COUNT"

if [ $SCREENSHOT_COUNT -gt 0 ]; then
  echo ""
  echo "📸 Screenshot files created:"
  ls -lh e2e-screenshots/*.png | awk '{print "   - " $9 " (" $5 ")"}'
fi

echo ""
echo "✅ E2E test execution complete"
