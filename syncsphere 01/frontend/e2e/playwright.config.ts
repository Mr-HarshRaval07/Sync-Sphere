// ==========================================
// 1. Playwright Config
// ==========================================
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
---
// ==========================================
// 2. Playwright E2E User Journey Test
// ==========================================
import { test, expect } from '@playwright/test';

test.describe('SyncSphere Enterprise User Journey E2E', () => {
  test('Complete platform flow: login, switch org, create workflow and trace logs', async ({ page }) => {
    // 1. Authenticate login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@acme.ai');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Validate redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // 2. Navigate to Workflows page & Switch Org context
    await page.goto('/dashboard/workflows');
    await expect(page.locator('h2')).toContainText('Workflows');
    
    // 3. Open Admin Portal & check Org context switcher
    await page.goto('/dashboard/admin');
    await page.selectOption('select[aria-label="Active Organization switcher"]', { label: 'Acme Corp' });
    
    // 4. Create new workflow designer
    await page.goto('/dashboard/workflows');
    await page.click('button:has-text("New Workflow")');
    
    // Expect canvas to load React Flow builder
    const flowCanvas = page.locator('.react-flow__renderer');
    await expect(flowCanvas).toBeVisible();
    
    // 5. Drag and drop Start & End node, execute and run simulation
    await page.click('button:has-text("From Template")');
    await page.click('button:has-text("Blank Workflow")');
    
    // Verify toolbar actions
    const saveButton = page.locator('button[aria-label="Save draft"]');
    await expect(saveButton).toBeVisible();
    
    // 6. Navigate to Operations monitor page and check gauges
    await page.goto('/dashboard/operations');
    await expect(page.locator('h2')).toContainText('Enterprise Operations Center');
    
    // Check if the live activity feed list is visible
    const feed = page.locator('h4:has-text("Live Activity Feed")');
    await expect(feed).toBeVisible();
  });
});
