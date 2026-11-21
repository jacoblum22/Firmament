import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { mockFramerMotion } from '../test/mocks/framerMotion';
import ExportButtons from './ExportButtons';

vi.mock('framer-motion', () => mockFramerMotion());

describe('ExportButtons', () => {
  it('calls handlers and shows feedback', () => {
    const copy = vi.fn();
    const download = vi.fn();

    const { rerender } = render(
      <ExportButtons
        handleCopyAsMarkdown={copy}
        handleDownloadMarkdown={download}
        isCopyExporting={false}
        isDownloadExporting={false}
        copyFeedbackVisible={false}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /copy as markdown/i }));
    fireEvent.click(screen.getByRole('button', { name: /download \.md/i }));
    expect(copy).toHaveBeenCalledTimes(1);
    expect(download).toHaveBeenCalledTimes(1);

    rerender(
      <ExportButtons
        handleCopyAsMarkdown={copy}
        handleDownloadMarkdown={download}
        isCopyExporting={true}
        isDownloadExporting={false}
        copyFeedbackVisible={true}
      />,
    );

    expect(screen.getByRole('button', { name: /exporting/i })).toBeDisabled();
    expect(screen.getByText('Copied!')).toBeInTheDocument();
  });
});
