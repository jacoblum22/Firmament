import { useCallback, useEffect, useRef, useState } from 'react';
import config from '../config';
import apiService, {
  TopicResponse,
  UploadResponse,
} from '../services/apiService';
import { validateFile } from '../components/UploadZone';
import { BulletExpansion, JobStatus, NestedExpansions } from './uploadPipelineTypes';
import useAbortController from './useAbortController';

export function useUploadPipeline() {
  const [file, setFile] = useState<File | null>(null);
  const [response, setResponse] = useState<UploadResponse | null>(null);
  const [topics, setTopics] = useState<TopicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [segmenting, setSegmenting] = useState(false);
  const [generatingHeadings, setGeneratingHeadings] = useState(false);
  const [activeHue, setActiveHue] = useState<number | null>(null);
  const [showProgressBar, setShowProgressBar] = useState(false);
  const [allowUnmount, setAllowUnmount] = useState(false);
  const [progressBarExited, setProgressBarExited] = useState(false);
  const [processedChunks, setProcessedChunks] = useState<{
    num_chunks: number;
    total_words: number;
  } | null>(null);
  const [expandedBullets, setExpandedBullets] = useState<NestedExpansions>({});
  const uploadInFlightRef = useRef(false);
  const progressEventSourceRef = useRef<EventSource | null>(null);
  const { abort, reset } = useAbortController();

  const closeProgressEventSource = useCallback(() => {
    if (progressEventSourceRef.current) {
      progressEventSourceRef.current.close();
      progressEventSourceRef.current = null;
    }
  }, []);

  const cancelProcessing = useCallback(() => {
    abort();
    closeProgressEventSource();
    uploadInFlightRef.current = false;
    setLoading(false);
    setStatus({ stage: 'idle' });
    setError(null);
    setSuccessMessage('Processing cancelled.');
  }, [abort, closeProgressEventSource]);

  useEffect(() => {
    return () => {
      closeProgressEventSource();
    };
  }, [closeProgressEventSource]);

  const memoizedGetAllTopicChunks = useCallback(
    (topicData: TopicResponse['topics'][string], allSegments?: Array<{ position: string; text: string }>): string[] => {
      if (!topicData.segment_positions || !allSegments) {
        return topicData.examples || [];
      }

      const segmentMap = new Map<string, string>();
      allSegments.forEach((segment) => {
        segmentMap.set(segment.position, segment.text);
      });

      return topicData.segment_positions
        .map((position: string) => segmentMap.get(position))
        .filter((chunk: string | undefined): chunk is string => Boolean(chunk));
    },
    []
  );

  const generateBulletKey = (bulletPoint: string): string => {
    const cleanBullet = bulletPoint.replace(/^[-*+]\s*/, '').trim();
    return cleanBullet.slice(0, 80);
  };

  const loadSavedExpansions = (topicsData: TopicResponse) => {
    const newExpandedBullets: Record<string, BulletExpansion> = {};

    Object.entries(topicsData.topics).forEach(([topicId, topic]) => {
      const bulletExpansions = topic.bullet_expansions;
      if (bulletExpansions) {
        Object.entries(bulletExpansions).forEach(([bulletKey, expansionData]) => {
          const originalBullet = expansionData.original_bullet || bulletKey;
          const frontendKey = `${topicId}_${generateBulletKey(originalBullet)}`;

          newExpandedBullets[frontendKey] = {
            expansion: {
              original_bullet: originalBullet,
              expanded_bullets: expansionData.expanded_bullets || [],
              topic_heading: expansionData.topic_heading || '',
              chunks_used: expansionData.chunks_used || 0,
              layer: expansionData.layer || 1,
            },
            subExpansions: {},
          };

          if (expansionData.sub_expansions) {
            Object.entries(expansionData.sub_expansions).forEach(([subKey, subExpansionData]) => {
              const originalSubBullet = subExpansionData.original_bullet || subKey;
              const subFrontendKey = `${frontendKey}_sub_${originalSubBullet.slice(0, 30)}`;

              if (!newExpandedBullets[frontendKey].subExpansions) {
                newExpandedBullets[frontendKey].subExpansions = {};
              }

              newExpandedBullets[frontendKey].subExpansions![subFrontendKey] = {
                expansion: {
                  original_bullet: originalSubBullet,
                  expanded_bullets: subExpansionData.expanded_bullets || [],
                  topic_heading: subExpansionData.topic_heading || '',
                  chunks_used: subExpansionData.chunks_used || 0,
                  layer: subExpansionData.layer || 2,
                },
                subExpansions: {},
              };
            });
          }
        });
      }
    });

    setExpandedBullets(newExpandedBullets);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];

      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        return;
      }

      setFile(selectedFile);
      setResponse(null);
      setTopics(null);
    }
  };

  const handleProcessChunks = async () => {
    if (!response?.text || !response.filename) return;

    setError(null);
    setSegmenting(true);
    try {
      const data = await apiService.processChunks(response.text, response.filename, response.processing_id);
      setProcessedChunks({
        num_chunks: data.num_chunks,
        total_words: data.total_words,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "We couldn't process your file chunks. Please try again.";
      setError(
        JSON.stringify({
          error: 'Processing failed',
          details: errorMessage,
          user_action: 'Please try uploading your file again.',
          error_code: 'chunk_processing_failed',
        })
      );
    } finally {
      setSegmenting(false);
    }
  };

  const handleGenerateHeadings = async () => {
    if (!response?.filename || !processedChunks) return;

    setGeneratingHeadings(true);
    setError(null);

    try {
      const data = await apiService.generateHeadings(response.filename, response.processing_id);
      setTopics(data);
      loadSavedExpansions(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "We couldn't generate topics for your content.";
      setError(
        JSON.stringify({
          error: 'Topic generation failed',
          details: errorMessage,
          user_action: 'Please ensure your file contains enough text content and try again.',
          error_code: 'topic_generation_failed',
        })
      );
    } finally {
      setGeneratingHeadings(false);
    }
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();

    if (uploadInFlightRef.current) {
      return;
    }

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length === 0) return;

    if (droppedFiles.length > 1) {
      setError(
        JSON.stringify({
          error: 'Multiple files detected',
          details: 'You can only upload one file at a time.',
          user_action: 'Please select just one file and try again.',
          error_code: 'multiple_files',
        })
      );
      return;
    }

    if (droppedFiles && droppedFiles.length > 0) {
      const droppedFile = droppedFiles[0];

      const validationError = validateFile(droppedFile);
      if (validationError) {
        setError(validationError);
        return;
      }

      setFile(droppedFile);
      setResponse(null);
      setTopics(null);

      const requestSignal = reset();
      uploadInFlightRef.current = true;
      setLoading(true);
      setError(null);
      setSuccessMessage(null);
      setStatus({ stage: 'uploading' });

      try {
        const formData = new FormData();
        formData.append('file', droppedFile);

        const headers: Record<string, string> = {};
        const token = localStorage.getItem('studymate_token');
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }

        const uploadResponse = await fetch(config.getApiUrl('upload'), {
          method: 'POST',
          body: formData,
          headers,
          signal: requestSignal,
        });

        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text();
          let message = `Upload failed with status ${uploadResponse.status}`;

          try {
            const parsed = JSON.parse(errorText) as { error?: string; message?: string };
            message = parsed.error || parsed.message || message;
          } catch {
            if (errorText) {
              message = errorText;
            }
          }

          throw new Error(message);
        }

        const data = (await uploadResponse.json()) as UploadResponse;
        setJobId(data.job_id);

        closeProgressEventSource();
        const evt = new EventSource(config.getApiUrl(`progress/${data.job_id}`));
        progressEventSourceRef.current = evt;
        evt.onmessage = (event) => {
          const parsed = JSON.parse(event.data);
          setStatus(parsed);

          if (parsed.stage === 'error') {
            const serverError = parsed.error || 'An error occurred during processing';
            setError(
              JSON.stringify({
                error: 'Processing failed',
                details: serverError,
                user_action: 'Please try uploading your file again.',
                error_code: 'server_processing_error',
              })
            );
          }

          if (parsed.stage === 'done' && parsed.result) {
            setResponse(parsed.result);
            if (parsed.result.topics) {
              const topicsData = { ...parsed.result, topics: parsed.result.topics };
              setTopics(topicsData);
              loadSavedExpansions(topicsData);

              if (parsed.result?.segments && Array.isArray(parsed.result.segments)) {
                const segments = parsed.result.segments;

                if (segments.length === 0) {
                  return;
                }

                const totalWords = segments.reduce((sum: number, segment: { text?: string }) => {
                  const text = segment?.text;
                  if (!text || typeof text !== 'string') {
                    return sum;
                  }

                  const words = text.split(/\s+/).filter((word) => word.length > 0);
                  return sum + words.length;
                }, 0);

                setProcessedChunks({
                  num_chunks: segments.length,
                  total_words: totalWords,
                });
              }
            }
          }

          if (['done', 'error'].includes(parsed.stage)) {
            uploadInFlightRef.current = false;
            evt.close();
            progressEventSourceRef.current = null;
          }
        };
        evt.onerror = () => {
          uploadInFlightRef.current = false;
          evt.close();
          progressEventSourceRef.current = null;

          if (!requestSignal.aborted) {
            setError(
              JSON.stringify({
                error: 'Connection lost',
                details: 'We lost connection to the server while processing your file.',
                user_action: 'Please check your internet connection and try uploading again.',
                error_code: 'connection_lost',
              })
            );
          }
        };
      } catch (err) {
        uploadInFlightRef.current = false;

        if (err instanceof Error && err.name === 'AbortError') {
          setStatus({ stage: 'idle' });
          setError(null);
          setSuccessMessage('Processing cancelled.');
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Upload failed';
          setError(
            JSON.stringify({
              error: 'Upload failed',
              details: errorMessage,
              user_action: 'Please check your internet connection and try again.',
              error_code: 'upload_failed',
            })
          );
        }
      } finally {
        setLoading(false);
      }
    }
  };

  const handleExpandCluster = async (clusterId: string) => {
    if (!response?.filename) return;

    setError(null);
    try {
      const data = await apiService.expandCluster({
        filename: response.filename,
        cluster_id: clusterId,
        processing_id: response?.processing_id,
      });
      const clusterData = data as { cluster?: { bullet_points?: string[] } };
      setTopics((prevTopics) => {
        if (!prevTopics) return prevTopics;

        const updatedTopics = { ...prevTopics.topics };
        updatedTopics[clusterId] = {
          ...updatedTopics[clusterId],
          bullet_points: clusterData.cluster?.bullet_points,
        };

        return { ...prevTopics, topics: updatedTopics };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to expand cluster.');
    }
  };

  const handleExpandBulletPoint = async (bulletPoint: string, topicId: string) => {
    if (!topics || !topics.topics[topicId]) return;

    const topic = topics.topics[topicId];
    const topicChunks = memoizedGetAllTopicChunks(topic, topics?.segments) || topic.examples || [];
    const topicHeading = topic.heading;

    try {
      const data = await apiService.expandBulletPoint({
        bullet_point: bulletPoint,
        chunks: topicChunks,
        topic_heading: topicHeading,
        filename: response?.filename || '',
        processing_id: response?.processing_id,
        topic_id: topicId,
        layer: 1,
      });

      if (!data.error) {
        const bulletKey = `${topicId}_${generateBulletKey(bulletPoint)}`;
        setExpandedBullets((prev) => ({
          ...prev,
          [bulletKey]: { expansion: data, subExpansions: {} },
        }));
      }
    } catch (err) {
      console.error('Failed to expand bullet point:', err);
    }
  };

  const handleExpandSubBulletPoint = async (
    subBullet: string,
    topicId: string,
    parentBulletKey: string,
    depth: number = 1
  ) => {
    if (depth >= 2) return;

    const topic = topics?.topics[topicId];
    if (!topic) return;

    const topicChunks = memoizedGetAllTopicChunks(topic, topics?.segments) || topic.examples || [];
    const topicHeading = topic.heading || `Topic ${topicId}`;

    try {
      const data = await apiService.expandBulletPoint({
        bullet_point: subBullet,
        chunks: topicChunks,
        topic_heading: topicHeading,
        filename: response?.filename || '',
        processing_id: response?.processing_id,
        topic_id: topicId,
        parent_bullet: parentBulletKey,
        layer: depth + 1,
      });

      if (!data.error) {
        const subBulletKey = `${parentBulletKey}_sub_${subBullet.slice(0, 30)}`;
        setExpandedBullets((prev) => {
          const updated = { ...prev };
          if (updated[parentBulletKey]) {
            if (!updated[parentBulletKey].subExpansions) {
              updated[parentBulletKey].subExpansions = {};
            }
            updated[parentBulletKey].subExpansions![subBulletKey] = {
              expansion: data,
              subExpansions: {},
            };
          }
          return updated;
        });
      }
    } catch (err) {
      console.error('Failed to expand sub-bullet point:', err);
    }
  };

  return {
    file,
    setFile,
    response,
    setResponse,
    topics,
    setTopics,
    error,
    setError,
    successMessage,
    setSuccessMessage,
    jobId,
    setJobId,
    status,
    setStatus,
    loading,
    setLoading,
    dragOver,
    setDragOver,
    segmenting,
    setSegmenting,
    generatingHeadings,
    setGeneratingHeadings,
    activeHue,
    setActiveHue,
    showProgressBar,
    setShowProgressBar,
    allowUnmount,
    setAllowUnmount,
    progressBarExited,
    setProgressBarExited,
    processedChunks,
    setProcessedChunks,
    expandedBullets,
    setExpandedBullets,
    handleFileChange,
    handleProcessChunks,
    handleGenerateHeadings,
    handleDrop,
    cancelProcessing,
    handleExpandCluster,
    handleExpandBulletPoint,
    handleExpandSubBulletPoint,
    generateBulletKey,
    loadSavedExpansions,
    memoizedGetAllTopicChunks,
  };
}
