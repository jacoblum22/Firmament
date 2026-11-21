import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { mockFramerMotion } from '../test/mocks/framerMotion';
import ActionButtons from './ActionButtons';

vi.mock('framer-motion', () => mockFramerMotion());

const buttonStyle = { border: 'none' };

describe('ActionButtons', () => {
  it('invokes segment handler and enables generate topics after chunks exist', () => {
    const onSegment = vi.fn();
    const onHeadings = vi.fn();

    const { rerender } = render(
      <ActionButtons
        handleProcessChunks={onSegment}
        handleGenerateHeadings={onHeadings}
        processedChunks={null}
        segmenting={false}
        generatingHeadings={false}
        buttonStyle={buttonStyle}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /segment & optimize transcript/i }));
    expect(onSegment).toHaveBeenCalled();

    expect(screen.getByRole('button', { name: /generate topics with ai/i })).toBeDisabled();

    rerender(
      <ActionButtons
        handleProcessChunks={onSegment}
        handleGenerateHeadings={onHeadings}
        processedChunks={{ chunks: [] }}
        segmenting={false}
        generatingHeadings={false}
        buttonStyle={buttonStyle}
      />,
    );

    const headingsBtn = screen.getByRole('button', { name: /generate topics with ai/i });
    expect(headingsBtn).not.toBeDisabled();
    fireEvent.click(headingsBtn);
    expect(onHeadings).toHaveBeenCalled();
  });
});
