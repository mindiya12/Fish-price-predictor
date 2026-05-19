import { test, expect } from '@playwright/test';

test.describe('FishPrice.LK - AI Fish Price Predictor', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/', { waitUntil: 'networkidle' });
    });

    test('✅ Page loads successfully with correct title', async ({ page }) => {
        await expect(page).toHaveTitle(/FishPrice|Fish Price Predictor|Balaya/);
        await expect(page.locator('h1')).toContainText('Fish Price Forecast');
    });

    test('✅ Historical price data loads', async ({ page }) => {
        // Wait for data to load
        await expect(page.locator('text=30-Day Price History')).toBeVisible();
        await expect(page.getByText(/Balaya|Peliyagoda/).first()).toBeVisible();

        // Check that at least one price value appears
        await expect(page.getByText(/\d{3,}/).first()).toBeVisible({ timeout: 15000 });
    });

    test('✅ 3-Day AI Predictions are displayed', async ({ page }) => {
        await expect(page.getByText(/Tomorrow|Day 1|Day 2|Day 3|3-day/i).first()).toBeVisible();
        await expect(page.getByText(/XGBoost/i).first()).toBeVisible();
    });

    test('✅ Confidence Bands section is present', async ({ page }) => {
        await expect(page.getByText(/Confidence Bands|upper|lower|bounds/i).first()).toBeVisible();
    });

    test('✅ CSV Download works correctly', async ({ page }) => {
        const downloadPromise = page.waitForEvent('download');

        await page.getByRole('button', { name: /Download 7-day data/i }).click();
        // Fallback if button text varies
        if (!(await page.getByRole('button', { name: /Download/i }).count())) {
            await page.getByText('Download 7-day data (CSV)').click();
        }

        const download = await downloadPromise;
        expect(download.suggestedFilename()).toMatch(/\.csv$/i);

        console.log(`✅ CSV downloaded: ${download.suggestedFilename()}`);
    });

    test('✅ Mobile Responsiveness', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.reload({ waitUntil: 'networkidle' });

        await expect(page.locator('text=30-Day Price History')).toBeVisible();
        // Charts and tables should not overflow
        await expect(page.locator('canvas, table').first()).toBeVisible();
    });

    test('✅ No JavaScript console errors', async ({ page }) => {
        const errors: string[] = [];
        page.on('console', msg => {
            if (msg.type() === 'error') errors.push(msg.text());
        });

        await page.reload({ waitUntil: 'networkidle' });
        expect(errors).toHaveLength(0);
    });

    test('✅ Performance - Page loads under 5 seconds', async ({ page }) => {
        const startTime = Date.now();
        await page.goto('/', { waitUntil: 'networkidle' });
        const loadTime = Date.now() - startTime;

        console.log(`⏱️ Page load time: ${loadTime}ms`);
        expect(loadTime).toBeLessThan(5000);
    });
});