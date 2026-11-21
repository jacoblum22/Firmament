import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConnectionStatus } from './ConnectionStatus';

vi.mock('../hooks/useNetworkStatus', () => ({
  useNetworkStatus: vi.fn(),
}));

import { useNetworkStatus } from '../hooks/useNetworkStatus';

describe('ConnectionStatus', () => {
  beforeEach(() => {
    vi.mocked(useNetworkStatus).mockReset();
  });

  it('renders nothing when fully online', () => {
    vi.mocked(useNetworkStatus).mockReturnValue({
      connectionState: {} as never,
      isFullyOnline: true,
      isOnline: true,
      isBackendReachable: true,
      isInitializing: false,
      latency: 10,
      errorCount: 0,
      retryAttempt: 0,
      forceHealthCheck: vi.fn(),
    });

    const { container } = render(<ConnectionStatus />);
    expect(container.firstChild).toBeNull();
  });

  it('shows offline message when browser offline', () => {
    vi.mocked(useNetworkStatus).mockReturnValue({
      connectionState: {} as never,
      isFullyOnline: false,
      isOnline: false,
      isBackendReachable: false,
      isInitializing: false,
      latency: undefined,
      errorCount: 0,
      retryAttempt: 0,
      forceHealthCheck: vi.fn(),
    });

    render(<ConnectionStatus />);
    expect(screen.getByRole('heading', { name: /no internet connection/i })).toBeInTheDocument();
  });
});
