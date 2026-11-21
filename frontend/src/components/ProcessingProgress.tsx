import { memo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { LegacyAnimationControls } from 'framer-motion';
import { JobStatus } from '../hooks/uploadPipelineTypes';

type ProcessingProgressProps = {
  status: JobStatus | null;
  showProgressBar: boolean;
  progressBarExited: boolean;
  allowUnmount: boolean;
  isFinishing: boolean;
  coreControls: LegacyAnimationControls;
  glowControls: LegacyAnimationControls;
  onExitComplete: () => void;
};

export function ProcessingProgress({
  status,
  showProgressBar,
  progressBarExited,
  allowUnmount,
  isFinishing,
  coreControls,
  glowControls,
  onExitComplete,
}: ProcessingProgressProps) {
  return (
    <AnimatePresence onExitComplete={onExitComplete}>
      {showProgressBar && (
        <motion.div
          key="progress"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={allowUnmount ? { opacity: 0, height: 0, transition: { duration: 0.4 } } : {}}
          transition={{ duration: 0.4 }}
          style={{
            overflow: 'hidden',
            marginTop: '1rem',
            paddingBottom: '60px',
            paddingLeft: '30px',
            paddingRight: '30px',
          }}
          data-progress-exited={progressBarExited}
        >
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            {status?.stage === 'uploading'
              ? 'Uploading file...'
              : status?.stage === 'preprocessing'
                ? 'Preprocessing audio...'
                : status?.stage === 'transcribing' &&
                    typeof status.current === 'number' &&
                    typeof status.total === 'number'
                    ? status.current === 0
                      ? `Transcribing… (${status.total} chunks; first chunk can take 1–3+ min on CPU)`
                      : `Transcribed ${status.current} of ${status.total} chunks…`
                  : status?.stage === 'saving_output'
                    ? 'Saving output...'
                    : isFinishing
                      ? 'Finishing up…'
                      : 'Beginning transcription…'}
          </motion.p>

          <div
            style={{
              position: 'relative',
              overflow: 'visible',
              padding: '20px clamp(20px, 5vw, 40px)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            <div className="neon-progress-wrapper">
              <motion.div
                className="neon-progress-core"
                initial={{ width: '0%', opacity: 0 }}
                animate={coreControls}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                style={{ position: 'absolute', left: 0, top: 0 }}
              />
              <motion.div
                className="neon-progress-glow"
                initial={{ width: '0%', opacity: 0 }}
                animate={glowControls}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                style={{ position: 'absolute', left: 0, top: 0 }}
              />
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default memo(ProcessingProgress);
