import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { mockFramerMotion } from '../test/mocks/framerMotion';
import { SignInScreen } from './SignInScreen';

vi.mock('./GoogleSignInButton', () => ({
  GoogleSignInButton: () => (
    <button type="button">
      Sign in with Google
    </button>
  ),
}));

vi.mock('framer-motion', () => mockFramerMotion());

describe('SignInScreen', () => {
  it('renders brand and sign-in control', () => {
    render(
      <SignInScreen
        isLoading={false}
        successMessage={null}
        setSuccessMessage={vi.fn()}
        setError={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument();
    expect(screen.getByText(/smarter studying starts here/i)).toBeInTheDocument();
  });
});
