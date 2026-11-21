import type { PropsWithChildren, ReactNode } from 'react';

/**
 * Stubs Framer Motion in Vitest so components render without layout/measure logic.
 * Import from tests via: vi.mock('framer-motion', () => mockFramerMotion())
 */
const Passthrough = ({ children, ...rest }: PropsWithChildren<Record<string, unknown>>) => (
  <div {...rest}>{children}</div>
);

const MotionButton = ({
  children,
  whileHover: _wH,
  whileTap: _wT,
  ...rest
}: PropsWithChildren<Record<string, unknown> & { whileHover?: unknown; whileTap?: unknown }>) => (
  <button type="button" {...rest}>
    {children}
  </button>
);

export function mockFramerMotion() {
  return {
    motion: {
      div: Passthrough,
      button: MotionButton,
      p: Passthrough,
      span: Passthrough,
    },
    AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
  };
}
