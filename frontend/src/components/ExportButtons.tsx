import { motion } from 'framer-motion';

interface ExportButtonsProps {
  handleCopyAsMarkdown: () => void;
  handleDownloadMarkdown: () => void;
  isCopyExporting: boolean;
  isDownloadExporting: boolean;
  copyFeedbackVisible: boolean;
}

export default function ExportButtons({
  handleCopyAsMarkdown,
  handleDownloadMarkdown,
  isCopyExporting,
  isDownloadExporting,
  copyFeedbackVisible,
}: ExportButtonsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      style={{
        marginTop: '1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.7rem',
        flexWrap: 'wrap',
      }}
    >
      <button
        onClick={handleCopyAsMarkdown}
        disabled={isCopyExporting}
        style={{
          background: 'transparent',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.3)',
          borderRadius: '10px',
          padding: '0.5rem 0.85rem',
          cursor: isCopyExporting ? 'not-allowed' : 'pointer',
          opacity: isCopyExporting ? 0.75 : 1,
        }}
      >
        {isCopyExporting ? 'Exporting...' : 'Copy as Markdown'}
      </button>
      <button
        onClick={handleDownloadMarkdown}
        disabled={isDownloadExporting}
        style={{
          background: 'transparent',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.3)',
          borderRadius: '10px',
          padding: '0.5rem 0.85rem',
          cursor: isDownloadExporting ? 'not-allowed' : 'pointer',
          opacity: isDownloadExporting ? 0.75 : 1,
        }}
      >
        {isDownloadExporting ? 'Exporting...' : 'Download .md'}
      </button>
      <span
        style={{
          minWidth: '62px',
          fontSize: '0.86rem',
          color: copyFeedbackVisible ? 'rgba(134, 239, 172, 1)' : 'rgba(255,255,255,0.65)',
          transition: 'color 0.2s ease',
        }}
      >
        {copyFeedbackVisible ? 'Copied!' : ''}
      </span>
    </motion.div>
  );
}
