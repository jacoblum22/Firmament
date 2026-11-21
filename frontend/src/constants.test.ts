import { describe, it, expect } from 'vitest';
import { ACCENT_HUES, BRAND, FILE_VALIDATION, UI } from './constants';

describe('constants', () => {
  it('brand strings are non-empty', () => {
    expect(BRAND.NAME.length).toBeGreaterThan(0);
    expect(BRAND.TAGLINE.length).toBeGreaterThan(0);
  });

  it('file validation whitelist is consistent', () => {
    expect(FILE_VALIDATION.MAX_SIZE_BYTES).toBe(FILE_VALIDATION.MAX_SIZE_MB * 1024 * 1024);
    expect(FILE_VALIDATION.ALLOWED_EXTENSIONS.every((e) => e.startsWith('.'))).toBe(true);
    expect(FILE_VALIDATION.ALLOWED_MIME_TYPES.length).toBeGreaterThan(0);
  });

  it('accent hues are bounded color indices', () => {
    expect(ACCENT_HUES.length).toBeGreaterThan(0);
    for (const h of ACCENT_HUES) {
      expect(h).toBeGreaterThanOrEqual(0);
      expect(h).toBeLessThanOrEqual(360);
    }
  });

  it('UI theme token looks like hex', () => {
    expect(UI.THEME_COLOR).toMatch(/^#[0-9a-f]{6}$/i);
  });
});
