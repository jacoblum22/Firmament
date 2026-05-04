import { useEffect, useRef, useState } from 'react';
import './App.css';
import VanillaTilt from 'vanilla-tilt';
import { motion, useAnimation } from 'framer-motion';
import { BRAND } from './constants';
import { ConnectionStatus } from './components/ConnectionStatus';
import { ConnectionScreen } from './components/ConnectionScreen';
import { AuthHeader, AuthHeaderHandle } from './components/AuthHeader';
import { ApiKeyBanner } from './components/ApiKeyBanner';
import { SignInScreen } from './components/SignInScreen';
import ErrorDisplay from './components/ErrorDisplay';
import { UploadZone } from './components/UploadZone';
import ProcessingProgress from './components/ProcessingProgress';
import TranscriptDisplay from './components/TranscriptDisplay';
import TopicResults from './components/TopicResults';
import ActionButtons from './components/ActionButtons';
import ExportButtons from './components/ExportButtons';
import SuccessToast from './components/SuccessToast';
import EmptyState from './components/EmptyState';
import { useNetworkStatus } from './hooks/useNetworkStatus';
import { useUploadPipeline } from './hooks/useUploadPipeline';
import { useTopicPersistence } from './hooks/useTopicPersistence';
import { copyToClipboard, downloadMarkdown, exportAsMarkdown } from './utils/exportTopics';
import { useAuth } from './contexts/AuthContext';

const buttonStyle: React.CSSProperties = {
  marginLeft: '1rem',
  padding: '0.5rem 1rem',
  color: 'white',
  border: 'none',
  cursor: 'pointer',
};

function App() {
  const [copyFeedbackVisible, setCopyFeedbackVisible] = useState(false);
  const [successToastVisible, setSuccessToastVisible] = useState(false);
  const [expandingBulletKey, setExpandingBulletKey] = useState<string | null>(null);
  const [isCopyExporting, setIsCopyExporting] = useState(false);
  const [isDownloadExporting, setIsDownloadExporting] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();
  const { isBackendReachable, isInitializing, forceHealthCheck } = useNetworkStatus();
  const authHeaderRef = useRef<AuthHeaderHandle>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dropZoneRef = useRef<HTMLDivElement | null>(null);
  const canvasTransferred = useRef(false);
  const particleWorkerRef = useRef<Worker | null>(null);
  const coreControls = useAnimation();
  const glowControls = useAnimation();
  const {
    topics: persistedTopics,
    setTopics: setPersistedTopics,
    expandedBullets: persistedExpandedBullets,
    setExpandedBullets: setPersistedExpandedBullets,
    lastSavedAt,
  } = useTopicPersistence();

  const {
    response,
    setResponse,
    topics: pipelineTopics,
    setTopics: setPipelineTopics,
    error,
    setError,
    successMessage,
    setSuccessMessage,
    status,
    dragOver,
    setDragOver,
    segmenting,
    generatingHeadings,
    activeHue,
    setActiveHue,
    showProgressBar,
    setShowProgressBar,
    allowUnmount,
    setAllowUnmount,
    progressBarExited,
    setProgressBarExited,
    processedChunks,
    setFile,
    expandedBullets: pipelineExpandedBullets,
    setExpandedBullets: setPipelineExpandedBullets,
    handleFileChange,
    handleProcessChunks,
    handleGenerateHeadings,
    handleDrop,
    cancelProcessing,
    handleExpandCluster,
    handleExpandBulletPoint,
    handleExpandSubBulletPoint,
    generateBulletKey,
  } = useUploadPipeline();

  const topics = pipelineTopics ?? persistedTopics;
  const expandedBullets = Object.keys(pipelineExpandedBullets).length
    ? pipelineExpandedBullets
    : persistedExpandedBullets;
  const hasTopics = Boolean(topics && Object.keys(topics.topics).length > 0);
  const isProcessingActive =
    status?.stage === 'uploading' || status?.stage === 'transcribing';
  const showEmptyState = !hasTopics && !isProcessingActive && !generatingHeadings;
  const displayTagline = `${BRAND.TAGLINE}.`;
  const hasInitializedToastTrackingRef = useRef(false);
  const previousHasTopicsRef = useRef(hasTopics);
  const previousStageRef = useRef(status?.stage);
  const previousGeneratingHeadingsRef = useRef(generatingHeadings);

  const isFinishing = status?.stage === 'done' && showProgressBar && !allowUnmount;
  const canShowTranscript = response && (!showProgressBar || progressBarExited);

  useEffect(() => {
    setPersistedTopics(pipelineTopics);
  }, [pipelineTopics, setPersistedTopics]);

  useEffect(() => {
    setPersistedExpandedBullets(pipelineExpandedBullets);
  }, [pipelineExpandedBullets, setPersistedExpandedBullets]);

  useEffect(() => {
    if (!pipelineTopics && persistedTopics) {
      setPipelineTopics(persistedTopics);
    }
  }, [pipelineTopics, persistedTopics, setPipelineTopics]);

  useEffect(() => {
    const pipelineExpandedCount = Object.keys(pipelineExpandedBullets).length;
    const persistedExpandedCount = Object.keys(persistedExpandedBullets).length;

    if (pipelineExpandedCount === 0 && persistedExpandedCount > 0) {
      setPipelineExpandedBullets(persistedExpandedBullets);
    }
  }, [pipelineExpandedBullets, persistedExpandedBullets, setPipelineExpandedBullets]);

  useEffect(() => {
    if (!copyFeedbackVisible) return;

    const timerId = window.setTimeout(() => {
      setCopyFeedbackVisible(false);
    }, 1400);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [copyFeedbackVisible]);

  useEffect(() => {
    if (!successToastVisible) return;

    const autoDismissTimer = window.setTimeout(() => {
      setSuccessToastVisible(false);
    }, 3000);

    return () => {
      window.clearTimeout(autoDismissTimer);
    };
  }, [successToastVisible]);

  useEffect(() => {
    if (!hasInitializedToastTrackingRef.current) {
      hasInitializedToastTrackingRef.current = true;
      previousHasTopicsRef.current = hasTopics;
      previousStageRef.current = status?.stage;
      previousGeneratingHeadingsRef.current = generatingHeadings;
      return;
    }

    const topicsBecameAvailable = !previousHasTopicsRef.current && hasTopics;
    const stageCompletedNow = previousStageRef.current !== 'done' && status?.stage === 'done' && hasTopics;
    const headingsFinishedNow = previousGeneratingHeadingsRef.current && !generatingHeadings && hasTopics;

    if (topicsBecameAvailable || stageCompletedNow || headingsFinishedNow) {
      setSuccessToastVisible(true);
    }

    previousHasTopicsRef.current = hasTopics;
    previousStageRef.current = status?.stage;
    previousGeneratingHeadingsRef.current = generatingHeadings;
  }, [hasTopics, status?.stage, generatingHeadings]);

  const handleCopyAsMarkdown = async () => {
    if (isCopyExporting) {
      return;
    }

    setIsCopyExporting(true);

    const markdown = exportAsMarkdown(topics, expandedBullets);
    const copied = await copyToClipboard(markdown);

    if (copied) {
      setCopyFeedbackVisible(true);
    }

    window.setTimeout(() => {
      setIsCopyExporting(false);
    }, 450);
  };

  const handleDownloadMarkdown = () => {
    if (isDownloadExporting) {
      return;
    }

    setIsDownloadExporting(true);
    const markdown = exportAsMarkdown(topics, expandedBullets);
    downloadMarkdown(markdown);

    window.setTimeout(() => {
      setIsDownloadExporting(false);
    }, 450);
  };

  const handleExpandBulletPointWithLoading = async (bulletPoint: string, topicId: string) => {
    const bulletKey = `${topicId}_${generateBulletKey(bulletPoint)}`;
    setExpandingBulletKey(bulletKey);

    try {
      await handleExpandBulletPoint(bulletPoint, topicId);
    } finally {
      setExpandingBulletKey(null);
    }
  };

  const handleExpandSubBulletPointWithLoading = async (
    subBullet: string,
    topicId: string,
    parentBulletKey: string,
    depth?: number
  ) => {
    const subBulletKey = `${parentBulletKey}_sub_${subBullet.slice(0, 30)}`;
    setExpandingBulletKey(subBulletKey);

    try {
      await handleExpandSubBulletPoint(subBullet, topicId, parentBulletKey, depth);
    } finally {
      setExpandingBulletKey(null);
    }
  };

  useEffect(() => {
    let fadeTimer: ReturnType<typeof setTimeout> | null = null;
    let collapseTimer: ReturnType<typeof setTimeout> | null = null;

    if (status?.stage === 'transcribing') {
      setShowProgressBar(true);
      setAllowUnmount(false);
      setProgressBarExited(false);

      if (typeof status.current === 'number' && typeof status.total === 'number') {
        const progress = (status.current / status.total) * 100;
        coreControls.start({ width: `${Math.max(progress, 2)}%`, opacity: 1, transition: { duration: 0.4, ease: 'easeOut' } });
        glowControls.start({ width: `${Math.max(progress, 2)}%`, opacity: 1, transition: { duration: 0.4, ease: 'easeOut' } });
      }
    } else {
      setShowProgressBar(false);
      setAllowUnmount(true);
      setProgressBarExited(true);
    }

    if (status?.stage === 'done') {
      coreControls.start({ width: '100%', opacity: 1, transition: { duration: 0.2 } });
      glowControls.start({ width: '100%', opacity: 1, transition: { duration: 0.2 } });

      fadeTimer = setTimeout(() => {
        coreControls.start({ opacity: 0, transition: { duration: 0.6 } });
        glowControls.start({ opacity: 0, transition: { duration: 0.6 } });

        collapseTimer = setTimeout(() => {
          setAllowUnmount(true);
          setShowProgressBar(false);
        }, 600);
      }, 2000);
    }

    return () => {
      if (fadeTimer) clearTimeout(fadeTimer);
      if (collapseTimer) clearTimeout(collapseTimer);
    };
  }, [status, coreControls, glowControls, setAllowUnmount, setProgressBarExited, setShowProgressBar]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof OffscreenCanvas === 'undefined') return;
    if (canvasTransferred.current) return;
    canvasTransferred.current = true;

    try {
      const dpr = window.devicePixelRatio || 1;
      const width = window.innerWidth * dpr;
      const height = window.innerHeight * dpr;
      const offscreen = canvas.transferControlToOffscreen();
      const worker = new Worker(new URL('./workers/particleWorker.ts', import.meta.url), { type: 'module' });
      particleWorkerRef.current = worker;
      worker.postMessage({ canvas: offscreen, width, height, dpr }, [offscreen]);
    } catch (err) {
      console.warn('OffscreenCanvas already transferred or failed:', err);
    }

    if (dropZoneRef.current) {
      VanillaTilt.init(dropZoneRef.current, {
        max: 3,
        speed: 500,
        scale: 1,
        glare: false,
        reverse: false,
      });
    }
  }, []);

  useEffect(() => {
    let lastScrollY = window.scrollY;
    const handleScroll = () => {
      const newScrollY = window.scrollY;
      const dy = newScrollY - lastScrollY;
      lastScrollY = newScrollY;
      particleWorkerRef.current?.postMessage({ type: 'scroll', dy });
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <canvas ref={canvasRef} style={{ position: 'fixed', top: 0, left: 0, zIndex: -1, pointerEvents: 'none' }}></canvas>

      {isInitializing || !isBackendReachable ? (
        <ConnectionScreen
          isInitializing={isInitializing}
          isBackendReachable={isBackendReachable}
          forceHealthCheck={forceHealthCheck}
        />
      ) : !isAuthenticated ? (
        <>
          <ConnectionStatus />
          <SignInScreen
            isLoading={isLoading}
            successMessage={successMessage}
            setSuccessMessage={setSuccessMessage}
            setError={setError}
          />
        </>
      ) : (
        <>
          <ConnectionStatus />
          <AuthHeader ref={authHeaderRef} />
          <ApiKeyBanner onOpenSettings={() => authHeaderRef.current?.openSettings()} />

          <div style={{ padding: '2rem', fontFamily: '"Outfit", sans-serif' }}>
            <div className="label fade-in" style={{ animationDelay: '0.2s', fontSize: '2rem', marginBottom: '0rem' }}>
              {BRAND.NAME}
            </div>
            <div className="glow-text fade-in" data-text={displayTagline} style={{ animationDelay: '0.4s', marginBottom: '-1rem' }}>
              {displayTagline}
            </div>

            {hasTopics && lastSavedAt && (
              <div style={{ marginTop: '1.25rem', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'rgba(255,255,255,0.65)' }}>
                Last saved: {new Date(lastSavedAt).toLocaleString()}
              </div>
            )}

            {showEmptyState && (
              <EmptyState message="Upload a lecture recording, PDF, or text file to generate study notes." />
            )}

            <UploadZone
              fileInputRef={fileInputRef}
              dropZoneRef={dropZoneRef}
              dragOver={dragOver}
              activeHue={activeHue}
              setDragOver={setDragOver}
              setActiveHue={setActiveHue}
              handleDrop={handleDrop}
              handleFileChange={handleFileChange}
              onExplode={() => particleWorkerRef.current?.postMessage({ type: 'explode' })}
            />

            <ErrorDisplay
              error={error}
              onDismiss={() => setError(null)}
              className="mb-4"
              actionButton={
                error?.includes('upload')
                  ? {
                      label: 'Try Again',
                      action: () => {
                        setError(null);
                        setFile(null);
                        setResponse(null);
                      },
                    }
                  : undefined
              }
            />

            <ProcessingProgress
              status={status}
              showProgressBar={showProgressBar}
              progressBarExited={progressBarExited}
              allowUnmount={allowUnmount}
              isFinishing={isFinishing}
              coreControls={coreControls}
              glowControls={glowControls}
              onExitComplete={() => setProgressBarExited(true)}
            />

            {isProcessingActive && (
              <div style={{ marginTop: '0.9rem', display: 'flex', justifyContent: 'center' }}>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={cancelProcessing}
                  style={{
                    background: 'transparent',
                    color: 'rgba(255,255,255,0.86)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    borderRadius: '10px',
                    padding: '0.5rem 0.9rem',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </motion.button>
              </div>
            )}

            {canShowTranscript && response && <TranscriptDisplay response={response} />}

            {canShowTranscript && (
              <ActionButtons
                handleProcessChunks={handleProcessChunks}
                handleGenerateHeadings={handleGenerateHeadings}
                processedChunks={processedChunks}
                segmenting={segmenting}
                generatingHeadings={generatingHeadings}
                buttonStyle={buttonStyle}
              />
            )}

            <TopicResults
              topics={topics}
              expandedBullets={expandedBullets}
              expandingBulletKey={expandingBulletKey}
              generateBulletKey={generateBulletKey}
              handleExpandCluster={handleExpandCluster}
              handleExpandBulletPoint={handleExpandBulletPointWithLoading}
              handleExpandSubBulletPoint={handleExpandSubBulletPointWithLoading}
            />

            {hasTopics && (
              <ExportButtons
                handleCopyAsMarkdown={handleCopyAsMarkdown}
                handleDownloadMarkdown={handleDownloadMarkdown}
                isCopyExporting={isCopyExporting}
                isDownloadExporting={isDownloadExporting}
                copyFeedbackVisible={copyFeedbackVisible}
              />
            )}
          </div>

          <SuccessToast visible={successToastVisible} message="Study notes generated successfully!" />
        </>
      )}
    </>
  );
}

export default App;
