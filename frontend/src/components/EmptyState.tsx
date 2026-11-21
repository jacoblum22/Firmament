import { motion } from 'framer-motion';

interface EmptyStateProps {
  message: string;
}

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      style={{
        maxWidth: '760px',
        margin: '1.5rem auto 1.25rem',
        padding: '1.1rem 1.2rem',
        borderRadius: '14px',
        border: '1px solid rgba(255,255,255,0.16)',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04))',
        backdropFilter: 'blur(10px)',
        color: 'rgba(255,255,255,0.92)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.9rem',
      }}
    >
      <span aria-hidden="true" style={{ fontSize: '1.2rem', opacity: 0.85 }}>
        ✦
      </span>
      <span style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>{message}</span>
    </motion.div>
  );
}
