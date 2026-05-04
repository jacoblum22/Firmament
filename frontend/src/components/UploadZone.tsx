import React, { memo } from 'react';
import { ACCENT_HUES, FILE_VALIDATION } from '../constants';

export const getFileExtension = (filename: string): string => {
  if (!filename || typeof filename !== 'string') {
    return '';
  }

  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === 0 || lastDotIndex === filename.length - 1) {
    return '';
  }

  const extension = filename.slice(lastDotIndex).toLowerCase().trim();

  if (!extension.startsWith('.') || extension.length < 2) {
    return '';
  }

  return extension;
};

export const validateFile = (file: File): string | null => {
  if (!file || !(file instanceof File)) {
    return JSON.stringify({
      error: 'Invalid file selection',
      details: 'The file could not be read properly.',
      user_action: 'Please try selecting the file again.',
      error_code: 'invalid_file',
    });
  }

  if (file.size > FILE_VALIDATION.MAX_SIZE_BYTES) {
    const maxMB = FILE_VALIDATION.MAX_SIZE_MB;
    const actualMB = (file.size / (1024 * 1024)).toFixed(1);
    return JSON.stringify({
      error: 'File too large for upload',
      details: `Your file is ${actualMB}MB, but the maximum allowed size is ${maxMB}MB.`,
      user_action: 'Try compressing your file or uploading a smaller version.',
      error_code: 'file_too_large',
    });
  }

  if (file.size === 0) {
    return JSON.stringify({
      error: 'File is empty',
      details: 'The selected file contains no data.',
      user_action: 'Please select a different file that contains content.',
      error_code: 'empty_file',
    });
  }

  const fileExtension = getFileExtension(file.name);
  if (!fileExtension) {
    return JSON.stringify({
      error: 'Unable to determine file type',
      details: "Your file doesn't have a recognizable extension.",
      user_action: `Please rename your file to include a valid extension: ${FILE_VALIDATION.ALLOWED_EXTENSIONS.join(', ')}`,
      error_code: 'missing_extension',
      supported_formats: FILE_VALIDATION.ALLOWED_EXTENSIONS,
    });
  }

  if (!(FILE_VALIDATION.ALLOWED_EXTENSIONS as readonly string[]).includes(fileExtension)) {
    return JSON.stringify({
      error: `Unsupported file type: ${fileExtension}`,
      details: "This file format isn't supported by our system.",
      user_action: 'Please convert your file to a supported format and try again.',
      error_code: 'unsupported_format',
      supported_formats: FILE_VALIDATION.ALLOWED_EXTENSIONS,
    });
  }

  return null;
};

type UploadZoneProps = {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  dropZoneRef: React.RefObject<HTMLDivElement | null>;
  dragOver: boolean;
  activeHue: number | null;
  setDragOver: React.Dispatch<React.SetStateAction<boolean>>;
  setActiveHue: React.Dispatch<React.SetStateAction<number | null>>;
  handleDrop: (e: React.DragEvent<HTMLDivElement>) => Promise<void>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onExplode?: () => void;
};

function UploadZoneInner({
  fileInputRef,
  dropZoneRef,
  dragOver,
  activeHue,
  setDragOver,
  setActiveHue,
  handleDrop,
  handleFileChange,
  onExplode,
}: UploadZoneProps) {
  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept={FILE_VALIDATION.ALLOWED_EXTENSIONS.join(',')}
        style={{ display: 'none' }}
      />

      <div
        ref={dropZoneRef}
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        style={{
          marginTop: '4rem',
          ...(dragOver &&
            activeHue !== null &&
            ({
              '--accent-hue': `${activeHue}`,
            } as React.CSSProperties)),
          borderColor: dragOver && activeHue !== null ? `hsl(${activeHue}, 100%, 60%)` : undefined,
        }}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();

          if (!dragOver) {
            setDragOver(true);

            const randomHue = ACCENT_HUES[Math.floor(Math.random() * ACCENT_HUES.length)];
            setActiveHue(randomHue);

            if (dropZoneRef.current) {
              dropZoneRef.current.style.transform = 'rotateX(3deg) rotateY(0deg) scale(1.03)';
            }
          }
        }}
        onDragLeave={() => {
          setDragOver(false);
          setActiveHue(null);

          if (dropZoneRef.current) {
            dropZoneRef.current.style.transform = '';
          }
        }}
        onDrop={(e) => {
          setDragOver(false);
          setActiveHue(null);

          if (dropZoneRef.current) {
            dropZoneRef.current.style.transform = '';
          }

          onExplode?.();
          handleDrop(e);
        }}
      >
        <div className="drop-zone-content">
          <div
            style={{
              fontSize: '3rem',
              marginBottom: '1.5rem',
              opacity: dragOver ? 1 : 0.7,
              transition: 'all 0.3s ease',
              transform: dragOver ? 'scale(1.1)' : 'scale(1)',
            }}
          >
            {dragOver ? '📂' : '📁'}
          </div>

          <h3
            style={{
              margin: '0 0 1rem 0',
              fontSize: '1.4rem',
              fontWeight: '600',
              color: '#fff',
              opacity: dragOver ? 1 : 0.9,
              transition: 'opacity 0.3s ease',
            }}
          >
            {dragOver ? 'Drop your file here!' : 'Upload Your Study Material'}
          </h3>

          <p
            style={{
              margin: '0 0 1.5rem 0',
              fontSize: '1rem',
              color: '#ccc',
              lineHeight: '1.5',
              opacity: dragOver ? 0.8 : 0.7,
              transition: 'opacity 0.3s ease',
            }}
          >
            {dragOver ? 'Release to start processing...' : 'Drag & drop your file here or click to browse'}
          </p>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.5rem',
              justifyContent: 'center',
              marginBottom: '1rem',
            }}
          >
            {FILE_VALIDATION.ALLOWED_EXTENSIONS.map((ext) => (
              <span
                key={ext}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: '#ddd',
                  padding: '0.3rem 0.8rem',
                  borderRadius: '20px',
                  fontSize: '0.8rem',
                  fontWeight: '500',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  opacity: dragOver ? 0.6 : 0.8,
                  transition: 'opacity 0.3s ease',
                }}
              >
                {ext}
              </span>
            ))}
          </div>

          <div
            style={{
              fontSize: '0.85rem',
              color: '#999',
              opacity: dragOver ? 0.6 : 0.8,
              transition: 'opacity 0.3s ease',
            }}
          >
            💡 Supports PDFs, audio files, and text documents
          </div>
        </div>
      </div>
    </>
  );
}

/** Memoized drop zone — use named import alongside other layout components. */
export const UploadZone = memo(UploadZoneInner);
