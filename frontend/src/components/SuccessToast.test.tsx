import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SuccessToast from './SuccessToast';

describe('SuccessToast', () => {
  it('shows message when visible', () => {
    render(<SuccessToast visible message="Saved." />);
    expect(screen.getByRole('status')).toHaveTextContent('Saved.');
  });
});
