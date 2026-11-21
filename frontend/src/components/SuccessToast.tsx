interface SuccessToastProps {
  visible: boolean;
  message: string;
}

export default function SuccessToast({ visible, message }: SuccessToastProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'fixed',
        left: '50%',
        bottom: '1.2rem',
        transform: `translateX(-50%) translateY(${visible ? '0' : '14px'})`,
        background: '#16a34a',
        color: '#ffffff',
        padding: '0.7rem 1rem',
        borderRadius: '10px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.28)',
        fontSize: '0.9rem',
        fontWeight: 600,
        opacity: visible ? 1 : 0,
        transition: 'opacity 220ms ease, transform 220ms ease',
        pointerEvents: 'none',
        zIndex: 1200,
      }}
    >
      {message}
    </div>
  );
}
