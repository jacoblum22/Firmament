import { describe, it, expect } from 'vitest';
import { FILE_VALIDATION } from '../constants';
import { getFileExtension, validateFile } from './UploadZone';

function makeFile(name: string, size: number): File {
  return new File([new Uint8Array(size)], name, {
    type: 'application/pdf',
    lastModified: Date.now(),
  });
}

describe('getFileExtension', () => {
  it('returns lowercase extension with dot', () => {
    expect(getFileExtension('notes.PDF')).toBe('.pdf');
    expect(getFileExtension('a/b/recording.mp3')).toBe('.mp3');
  });

  it('returns empty for invalid names', () => {
    expect(getFileExtension('')).toBe('');
    expect(getFileExtension('.hidden')).toBe('');
    expect(getFileExtension('nodot')).toBe('');
  });
});

describe('validateFile', () => {
  it('accepts allowed extension under max size', () => {
    const f = makeFile('doc.pdf', 1024);
    expect(validateFile(f)).toBeNull();
  });

  it('rejects oversize files', () => {
    const f = makeFile('big.pdf', 1024);
    Object.defineProperty(f, 'size', {
      value: FILE_VALIDATION.MAX_SIZE_BYTES + 1,
      configurable: true,
    });
    const err = validateFile(f);
    expect(err).toBeTruthy();
    expect(err!).toContain('file_too_large');
  });

  it('rejects unsupported extension', () => {
    const f = makeFile('x.exe', 100);
    const err = validateFile(f);
    expect(err).toBeTruthy();
    expect(err!).toContain('unsupported_format');
  });
});
