import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { mockFramerMotion } from '../test/mocks/framerMotion';
import ErrorDisplay from './ErrorDisplay';

vi.mock('framer-motion', () => mockFramerMotion());

describe('ErrorDisplay', () => {
  it('renders nothing when error is null', () => {
    const { container } = render(<ErrorDisplay error={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('shows plain string errors', () => {
    render(<ErrorDisplay error="Something broke" />);
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('parses JSON error payloads', () => {
    render(
      <ErrorDisplay
        error={JSON.stringify({
          error: 'Failed',
          details: 'More info',
          user_action: 'Retry',
        })}
      />,
    );

    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText(/more info/i)).toBeInTheDocument();
  });

  it('calls onDismiss and action button', () => {
    const onDismiss = vi.fn();
    const onAction = vi.fn();

    render(
      <ErrorDisplay
        error="Oops"
        onDismiss={onDismiss}
        actionButton={{ label: 'Fix it', action: onAction }}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /dismiss error/i }));
    expect(onDismiss).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /fix it/i }));
    expect(onAction).toHaveBeenCalled();
  });
});
