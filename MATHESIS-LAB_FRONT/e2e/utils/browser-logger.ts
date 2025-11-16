import { Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Browser Logger Utility
 * Captures all browser console messages and network errors during Playwright tests
 * Logs are collected in memory and can be exported to JSON for test reports
 */

export interface BrowserLog {
  type: string;
  message: string;
  timestamp: string;
  location?: string;
}

export interface NetworkError {
  url: string;
  status: number;
  statusText: string;
}

export class BrowserLogger {
  private consoleLogs: BrowserLog[] = [];
  private networkErrors: NetworkError[] = [];
  private page: Page | null = null;

  /**
   * Initialize browser logger for a page
   * Attaches listeners for console messages, errors, and network failures
   */
  public initialize(page: Page): void {
    this.page = page;
    this.consoleLogs = [];
    this.networkErrors = [];

    // Capture browser console messages
    page.on('console', (msg) => {
      const timestamp = new Date().toLocaleTimeString();
      const location = msg.location();
      const logEntry: BrowserLog = {
        type: msg.type(),
        message: msg.text(),
        timestamp,
        location: location ? `${location.url}:${location.lineNumber}` : undefined,
      };
      this.consoleLogs.push(logEntry);
    });

    // Capture uncaught exceptions
    page.on('pageerror', (error) => {
      const timestamp = new Date().toLocaleTimeString();
      const logEntry: BrowserLog = {
        type: 'error',
        message: `Uncaught: ${error.message}`,
        timestamp,
        location: error.stack ? error.stack.split('\n')[1] : undefined,
      };
      this.consoleLogs.push(logEntry);
    });

    // Capture failed network requests
    page.on('response', (response) => {
      if (response.status() >= 400) {
        const networkError: NetworkError = {
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        };
        this.networkErrors.push(networkError);
      }
    });
  }

  /**
   * Get all console logs collected so far
   */
  public getConsoleLogs(): BrowserLog[] {
    return [...this.consoleLogs];
  }

  /**
   * Get all network errors collected so far
   */
  public getNetworkErrors(): NetworkError[] {
    return [...this.networkErrors];
  }

  /**
   * Clear all collected logs
   */
  public clear(): void {
    this.consoleLogs = [];
    this.networkErrors = [];
  }

  /**
   * Export logs to JSON file
   */
  public exportToJSON(outputPath: string, testName: string, duration: number): void {
    const logsData = {
      testName,
      duration,
      timestamp: new Date().toISOString(),
      consoleLogs: this.consoleLogs,
      networkErrors: this.networkErrors,
      summary: {
        totalLogs: this.consoleLogs.length,
        errorCount: this.consoleLogs.filter((l) => l.type === 'error').length,
        warningCount: this.consoleLogs.filter((l) => l.type === 'warning').length,
        networkErrorCount: this.networkErrors.length,
      },
    };

    // Create directory if it doesn't exist
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(logsData, null, 2));
  }

  /**
   * Get summary statistics
   */
  public getSummary() {
    return {
      totalConsoleLogs: this.consoleLogs.length,
      errors: this.consoleLogs.filter((l) => l.type === 'error'),
      warnings: this.consoleLogs.filter((l) => l.type === 'warning'),
      totalNetworkErrors: this.networkErrors.length,
    };
  }
}

export const browserLogger = new BrowserLogger();
