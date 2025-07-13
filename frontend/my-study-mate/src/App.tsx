import { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";
import VanillaTilt from "vanilla-tilt";
import { motion, AnimatePresence, useAnimation } from "framer-motion";
import ReactMarkdown from 'react-markdown';
import config from './config';
import { ConnectionStatus } from './components/ConnectionStatus';
import { useNetworkStatus } from './hooks/useNetworkStatus';
import apiService from './services/apiService';

const ACCENT_HUES = [185, 315, 35]; // cyan, pink, peach

type UploadResponse = {
  filename: string;
  filetype: string;
  message: string;
  text?: string;
  transcription_file?: string;
};

type DebugResult = {
  bullet_point: string;
  top_similar_chunks: { chunk: string; similarity: number }[];
  most_similar_chunk: string;
  similarity_to_current_topic: number;
  topic_similarities: { [key: string]: number };
};

type ExpandedBulletResult = {
  original_bullet: string;
  expanded_bullets: string[];  // Changed from expanded_content to expanded_bullets
  topic_heading: string;
  chunks_used: number;
};

type NestedExpansions = {
  [bulletKey: string]: {
    expansion: ExpandedBulletResult;
    subExpansions?: NestedExpansions;
  };
};

type BulletExpansion = {
  expansion: ExpandedBulletResult;
  subExpansions?: NestedExpansions;
};

type TopicResponse = {
  num_chunks: number;
  num_topics: number;
  total_tokens_used: number;
  segments?: Array<{ position: string; text: string }>; // Added segments
  topics: {
    [key: string]: {
      concepts: string[];
      heading: string;
      summary: string;
      keywords: string[];
      examples: string[];
      segment_positions?: string[]; // Added segment_positions
      stats: {
        num_chunks: number;
        min_size: number;
        mean_size: number;
        max_size: number;
      };
      bullet_points?: string[];
      bullet_expansions?: {
        [bulletKey: string]: {
          original_bullet?: string;
          expanded_bullets: string[];
          layer: number;
          topic_heading: string;
          chunks_used: number;
          timestamp: string;
          sub_expansions?: {
            [subBulletKey: string]: {
              original_bullet?: string;
              expanded_bullets: string[];
              layer: number;
              topic_heading: string;
              chunks_used: number;
              timestamp: string;
            };
          };
        };
      };
      debugResult?: DebugResult;
    };
  };
};

const buttonStyle: React.CSSProperties = {
  marginLeft: "1rem",
  padding: "0.5rem 1rem",
  color: "white",
  border: "none",
  cursor: "pointer",
};

function App() {
  const [, setFile] = useState<File | null>(null);
  const [response, setResponse] = useState<UploadResponse | null>(null);
  const [topics, setTopics] = useState<TopicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [, setJobId] = useState<string | null>(null);
  type JobStatus =
    | { stage: "uploading" | "preprocessing" | "saving_output" }
    | { stage: "transcribing"; current: number; total: number }
    | { stage: "done"; result: UploadResponse }
    | { stage: "error"; error: string };
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [generatingHeadings, setGeneratingHeadings] = useState(false);
  const [activeHue, setActiveHue] = useState<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dropZoneRef = useRef<HTMLDivElement | null>(null);
  const [showProgressBar, setShowProgressBar] = useState(false);
  const [allowUnmount, setAllowUnmount] = useState(false);
  const [progressBarExited, setProgressBarExited] = useState(false);
  const [processedChunks, setProcessedChunks] = useState<{
    num_chunks: number;
    total_words: number;
  } | null>(null);
  const [isDeveloperMode, setIsDeveloperMode] = useState(false);
  const [expandedBullets, setExpandedBullets] = useState<NestedExpansions>({});

  // Network status for connection handling
  const { isBackendReachable, isInitializing, forceHealthCheck } = useNetworkStatus();

  // Connection Screen Component
  const ConnectionScreen = () => (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      fontFamily: '"Outfit", sans-serif',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
      color: '#fff'
    }}>
      {/* Logo/Branding */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="label"
        style={{ 
          fontSize: '3rem',
          marginBottom: '1rem',
          textAlign: 'center'
        }}
      >
        MyStudyMate
      </motion.div>

      {/* Status Message */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{
          textAlign: 'center',
          marginBottom: '3rem'
        }}
      >
        <div style={{
          fontSize: '1.5rem',
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, hsl(185, 100%, 70%), hsl(315, 100%, 70%))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Connecting to StudyMate...
        </div>
        
        {/* Animated dots */}
        <div style={{ fontSize: '1.2rem', color: '#888' }}>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
          >
            •
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
            style={{ margin: '0 0.5rem' }}
          >
            •
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 1 }}
          >
            •
          </motion.span>
        </div>
      </motion.div>

      {/* Status Details */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '2rem',
          backdropFilter: 'blur(10px)',
          textAlign: 'center',
          maxWidth: '400px',
          marginBottom: '2rem'
        }}
      >
        <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>
          {!navigator.onLine ? (
            <>
              <div style={{ color: '#ff6b6b', marginBottom: '0.5rem' }}>
                🌐 No Internet Connection
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Please check your internet connection and try again.
              </div>
            </>
          ) : isInitializing ? (
            <>
              <div style={{ color: '#6bcf7f', marginBottom: '0.5rem' }}>
                ✅ Establishing Connection
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Just a moment while we connect to StudyMate...
              </div>
            </>
          ) : !isBackendReachable ? (
            <>
              <div style={{ color: '#ffd93d', marginBottom: '0.5rem' }}>
                🔧 Backend Unavailable
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                The StudyMate server is currently unreachable. We're working to reconnect automatically.
              </div>
            </>
          ) : (
            <>
              <div style={{ color: '#6bcf7f', marginBottom: '0.5rem' }}>
                ✅ Connection Established
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Connected to StudyMate! Redirecting...
              </div>
            </>
          )}
        </div>
      </motion.div>

      {/* Retry Button */}
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={forceHealthCheck}
        style={{
          background: 'linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))',
          border: 'none',
          borderRadius: '12px',
          padding: '1rem 2rem',
          color: '#fff',
          fontSize: '1.1rem',
          fontWeight: '600',
          cursor: 'pointer',
          boxShadow: '0 4px 20px rgba(0, 150, 255, 0.3)',
          fontFamily: 'inherit'
        }}
      >
        🔄 Retry Connection
      </motion.button>

      {/* Footer message */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        style={{
          marginTop: '3rem',
          color: '#666',
          fontSize: '0.9rem',
          textAlign: 'center'
        }}
      >
        StudyMate automatically retries the connection every few seconds.
      </motion.div>
    </div>
  );

  // Memoize the getAllTopicChunks function to prevent recreating it on every render
  const memoizedGetAllTopicChunks = useCallback((
    topicData: TopicResponse['topics'][string], 
    allSegments?: Array<{ position: string; text: string }>,
    topicId?: string,
    context?: string
  ): string[] => {
    const contextLabel = context || "getAllTopicChunks";
    console.log(`🔍 ${contextLabel} called for topic ${topicId || 'unknown'}`);
    console.log(`📊 ${contextLabel} topic data available:`, {
      hasSegmentPositions: !!topicData.segment_positions,
      segmentPositionsCount: topicData.segment_positions?.length || 0,
      examplesCount: topicData.examples?.length || 0,
      hasAllSegments: !!allSegments,
      allSegmentsCount: allSegments?.length || 0
    });

    if (!topicData.segment_positions || !allSegments) {
      console.warn(`⚠️ ${contextLabel}: Missing segment_positions or segments data, falling back to examples`);
      console.log(`📝 ${contextLabel} fallback: Using ${topicData.examples?.length || 0} examples instead`);
      return topicData.examples || [];
    }
    
    // Create a lookup map for faster access
    const segmentMap = new Map<string, string>();
    allSegments.forEach(segment => {
      segmentMap.set(segment.position, segment.text);
    });
    console.log(`🗂️ ${contextLabel}: Created segment lookup map with ${segmentMap.size} positions`);
    
    // Extract all chunks for this topic
    const topicChunks = topicData.segment_positions
      .map((position: string) => segmentMap.get(position))
      .filter((chunk: string | undefined): chunk is string => Boolean(chunk));
    
    const improvement = topicChunks.length - (topicData.examples?.length || 0);
    console.log(`🎯 ${contextLabel}: Successfully extracted ${topicChunks.length} chunks for topic ${topicId || 'unknown'}`);
    console.log(`📈 ${contextLabel} improvement: +${improvement} chunks over examples (${topicData.examples?.length || 0} -> ${topicChunks.length})`);
    
    // Log first few chunks for verification (only for main expansion, not debug)
    if (context === "Expansion" && topicChunks.length > 0) {
      console.log(`📄 First chunk preview: "${topicChunks[0].substring(0, 100)}..."`);
      if (topicChunks.length > 1) {
        console.log(`📄 Last chunk preview: "${topicChunks[topicChunks.length - 1].substring(0, 100)}..."`);
      }
    }
    
    return topicChunks;
  }, []);

  // File validation utility
  const validateFile = (file: File): string | null => {
    // Check file size (50MB for dev, 100MB for prod)
    const maxSize = 100 * 1024 * 1024; // 100MB in bytes
    if (file.size > maxSize) {
      return `File too large. Maximum size: ${maxSize / (1024 * 1024)}MB, your file: ${(file.size / (1024 * 1024)).toFixed(1)}MB`;
    }

    // Check file type
    const allowedTypes = ['.pdf', '.mp3', '.wav', '.txt', '.m4a'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
      return `Unsupported file type: ${fileExtension}. Supported types: ${allowedTypes.join(', ')}`;
    }

    // Check if file is empty
    if (file.size === 0) {
      return 'File is empty. Please select a valid file.';
    }

    return null; // No errors
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      
      // Validate the selected file
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
    try {
      const data = await apiService.processChunks(response.text, response.filename);
      setProcessedChunks({
        num_chunks: data.num_chunks,
        total_words: data.total_words,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to process chunks.");
    }
  };

  const handleGenerateHeadings = async () => {
    if (!response?.filename || !processedChunks) return;

    setGeneratingHeadings(true);
    setError(null);

    try {
      const data = await apiService.generateHeadings(response.filename);
      // Cast to the expected type since apiService has generic types
      const topicsData = data as TopicResponse;
      setTopics(topicsData);
      // Load saved expansions when topics are loaded
      loadSavedExpansions(topicsData);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to generate headings.");
    } finally {
      setGeneratingHeadings(false);
    }
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length === 0) return;

    if (droppedFiles.length > 1) {
      setError("Please upload only one file at a time.");
      return;
    }

    if (droppedFiles && droppedFiles.length > 0) {
      const file = droppedFiles[0];

      // Validate the dropped file
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      setFile(file);
      setResponse(null);
      setTopics(null);

      // Immediately upload the file
      setLoading(true);
      setError(null);

      try {
        const data = await apiService.uploadFile(file);
        setJobId(data.job_id);

        const evt = new EventSource(
          config.getApiUrl(`progress/${data.job_id}`)
        );
        evt.onmessage = (event) => {
          const parsed = JSON.parse(event.data);
          setStatus(parsed);

          // Once done, set final result into response state
          if (parsed.stage === "done" && parsed.result) {
            setResponse(parsed.result);
            if (parsed.result.topics) {
              const topicsData = { ...parsed.result, topics: parsed.result.topics };
              setTopics(topicsData);
              // Load saved expansions when topics are loaded from upload
              loadSavedExpansions(topicsData);
            }
          }

          // Auto-close when finished
          if (["done", "error"].includes(parsed.stage)) {
            evt.close();
          }
        };
        evt.onerror = () => {
          evt.close();
          setError("Lost connection to server. Please check your network connection and try again.");
        };
      } catch (error) {
        setError(error instanceof Error ? error.message : "Upload failed. Please try again.");
      } finally {
        setLoading(false);
      }
    }
  };

  const isFinishing =
    status?.stage === "done" && showProgressBar && !allowUnmount;

  const canShowTranscript = response && (!showProgressBar || progressBarExited);

  const coreControls = useAnimation();
  const glowControls = useAnimation();

  const canvasTransferred = useRef(false);
  const particleWorkerRef = useRef<Worker | null>(null);
  useEffect(() => {
    const canvas = canvasRef.current;

    // Only show progress bar when there's an actual transcription process
    if (status?.stage === "transcribing") {
      setShowProgressBar(true);
      setAllowUnmount(false);
      setProgressBarExited(false);
      
      if (typeof status.current === "number" && typeof status.total === "number") {
        const progress = (status.current / status.total) * 100;

        coreControls.start({
          width: `${Math.max(progress, 2)}%`,
          opacity: 1,
          transition: { duration: 0.4, ease: "easeOut" },
        });

        glowControls.start({
          width: `${Math.max(progress, 2)}%`,
          opacity: 1,
          transition: { duration: 0.4, ease: "easeOut" },
        });
      }
    } else {
      // Hide progress bar when no real process is running
      setShowProgressBar(false);
      setAllowUnmount(true);
      setProgressBarExited(true);
    }

    if (status?.stage === "done") {
      coreControls.start({
        width: "100%",
        opacity: 1,
        transition: { duration: 0.2 },
      });
      glowControls.start({
        width: "100%",
        opacity: 1,
        transition: { duration: 0.2 },
      });

      // Wait for fade-out before hiding
      setTimeout(() => {
        // ✅ Step 2: fade the bar out
        coreControls.start({
          opacity: 0,
          transition: { duration: 0.6 },
        });
        glowControls.start({
          opacity: 0,
          transition: { duration: 0.6 },
        });

        // ✅ Step 3: after fade finishes, collapse the container
        setTimeout(() => {
          setAllowUnmount(true);
          setShowProgressBar(false);
        }, 600); // wait for bar fade-out to finish
      }, 2000);
    }

    // Canvas and particle system initialization
    if (!canvas || typeof OffscreenCanvas === "undefined") return;

    if (canvasTransferred.current) return; // 🔐 prevent second transfer
    canvasTransferred.current = true;

    try {
      const dpr = window.devicePixelRatio || 1;
      const width = window.innerWidth * dpr;
      const height = window.innerHeight * dpr;

      // ✅ Define the variables you're about to use
      const offscreen = canvas.transferControlToOffscreen();
      const worker = new Worker(
        new URL("./particleWorker2.ts", import.meta.url),
        {
          type: "module",
        }
      );
      particleWorkerRef.current = worker;

      worker.postMessage(
        {
          canvas: offscreen,
          width,
          height,
          dpr,
        },
        [offscreen] // transfer ownership
      );
    } catch (err) {
      console.warn("OffscreenCanvas already transferred or failed:", err);
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
  }, [status, coreControls, glowControls, status?.stage]);

  useEffect(() => {
    let lastScrollY = window.scrollY;

    const handleScroll = () => {
      const newScrollY = window.scrollY;
      const dy = newScrollY - lastScrollY;
      lastScrollY = newScrollY;

      particleWorkerRef.current?.postMessage({
        type: "scroll",
        dy,
      });
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []); // ✅ empty deps: attach once, don't re-run

  const handleExpandCluster = async (clusterId: string) => {
    if (!response?.filename) return;

    setError(null);
    try {
      const data = await apiService.expandCluster({
        filename: response.filename,
        cluster_id: clusterId,
      });
      const clusterData = data as { cluster?: { bullet_points?: string[] } }; // Type assertion for legacy API
      console.log("Received bullet points:", clusterData.cluster?.bullet_points);
      // Update the specific topic with the expanded cluster data
      setTopics((prevTopics) => {
        if (!prevTopics) return prevTopics;

        const updatedTopics = { ...prevTopics.topics };
        updatedTopics[clusterId] = {
          ...updatedTopics[clusterId],
          bullet_points: clusterData.cluster?.bullet_points,
        };

        return { ...prevTopics, topics: updatedTopics };
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to expand cluster.");
    }
  };

  const handleDebugBulletPoint = async (bulletPoint: string, topicId: string) => {
    console.log("🔍 Debug bullet point clicked:", { bulletPoint, topicId });
    
    if (!topics || !topics.topics[topicId]) {
      console.error("❌ No topics or topic not found:", { topics: !!topics, topicExists: !!topics?.topics[topicId] });
      return;
    }

    const topic = topics.topics[topicId];
    
    // Try to get all chunks, fallback to examples if not available
    const topicChunks = memoizedGetAllTopicChunks(topic, topics?.segments, topicId, "Debug") || topic.examples || [];
    
    // Convert topics to the structure expected by the backend
    const allTopics = Object.keys(topics.topics).reduce((acc, id) => {
      const topicData = topics.topics[id];
      const chunks = memoizedGetAllTopicChunks(topicData, topics?.segments, id, "Debug-All") || topicData.examples || [];
      acc[id] = {
        examples: chunks, // Use all chunks, not just examples
        heading: topicData.heading
      };
      return acc;
    }, {} as { [key: string]: { examples: string[], heading: string } });

    console.log("📊 Request data:", { 
      bullet_point: bulletPoint,
      chunks_count: topicChunks?.length || 0,
      topics_count: Object.keys(allTopics).length 
    });

    try {
      const res = await fetch(config.getApiUrl("debug-bullet-point"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bullet_point: bulletPoint,
          chunks: topicChunks,
          topics: allTopics,
        }),
      });

      if (!res.ok) {
        console.error("❌ HTTP error:", res.status, res.statusText);
        const errorText = await res.text();
        console.error("Error response:", errorText);
        return;
      }

      const data = await res.json();
      console.log("📥 Backend response:", data);

      if (data.error) {
        console.error("Error debugging bullet point:", data.error);
      } else {
        console.log("✅ Debugging result received:", data);
        // Display the result below the bullet point
        setTopics((prevTopics) => {
          if (!prevTopics) {
            console.error("❌ No prevTopics in setState");
            return prevTopics;
          }

          const updatedTopics = { ...prevTopics.topics };
          updatedTopics[topicId] = {
            ...updatedTopics[topicId],
            debugResult: data, // Add debug result to the topic
          };

          console.log("🔄 Updated topic with debug result:", updatedTopics[topicId]);
          return { ...prevTopics, topics: updatedTopics };
        });
      }
    } catch (error) {
      console.error("Failed to debug bullet point:", error);
    }
  };

  const handleExpandBulletPoint = async (bulletPoint: string, topicId: string) => {
    console.log("🔧 Expand bullet point clicked:", { bulletPoint, topicId });
    
    if (!topics || !topics.topics[topicId]) {
      console.error("❌ No topics or topic not found:", { topics: !!topics, topicExists: !!topics?.topics[topicId] });
      return;
    }

    const topic = topics.topics[topicId];
    
    // Try to get all chunks, fallback to examples if not available
    const topicChunks = memoizedGetAllTopicChunks(topic, topics?.segments, topicId, "Expansion") || topic.examples || [];
    const topicHeading = topic.heading;

    console.log("📊 Expansion request data:", { 
      bullet_point: bulletPoint,
      chunks_count: topicChunks?.length || 0,
      topic_heading: topicHeading 
    });

    try {
      const res = await fetch(config.getApiUrl("expand-bullet-point"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bullet_point: bulletPoint,
          chunks: topicChunks,
          topic_heading: topicHeading,
          filename: response?.filename, // Add filename for saving
          topic_id: topicId, // Add topic_id for saving
          layer: 1, // First expansion layer
        }),
      });

      if (!res.ok) {
        console.error("❌ HTTP error:", res.status, res.statusText);
        const errorText = await res.text();
        console.error("Error response:", errorText);
        return;
      }

      const data = await res.json();
      console.log("📥 Backend expansion response:", data);

      if (data.error) {
        console.error("Error expanding bullet point:", data.error);
      } else {
        console.log("✅ Expansion result received:", data);
        // Store the expansion result using a consistent key generation
        const bulletKey = `${topicId}_${generateBulletKey(bulletPoint)}`;
        console.log(`🔑 Generated frontend expansion key: '${bulletKey}'`);
        
        setExpandedBullets(prev => ({
          ...prev,
          [bulletKey]: {
            expansion: data,
            subExpansions: {}
          }
        }));
      }
    } catch (error) {
      console.error("Failed to expand bullet point:", error);
    }
  };

  const handleExpandSubBulletPoint = async (
    subBullet: string, 
    topicId: string, 
    parentBulletKey: string,
    depth: number = 1
  ) => {
    // Prevent infinite recursion by limiting depth to maximum 2 layers
    if (depth >= 2) {
      console.log("Maximum expansion depth of 2 layers reached");
      return;
    }

    console.log("🔍 Expanding sub-bullet:", subBullet);
    console.log("Parent bullet key:", parentBulletKey);
    console.log("Expansion depth:", depth);

    const topic = topics?.topics[topicId];
    if (!topic) {
      console.error("Topic not found for expansion:", topicId);
      return;
    }

    // Try to get all chunks, fallback to examples if not available
    const topicChunks = memoizedGetAllTopicChunks(topic, topics?.segments, topicId, "Sub-bullet Expansion") || topic.examples || [];
    const topicHeading = topic.heading || `Topic ${topicId}`;

    try {
      const res = await fetch(config.getApiUrl("expand-bullet-point"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bullet_point: subBullet,
          chunks: topicChunks,
          topic_heading: topicHeading,
          filename: response?.filename, // Add filename for saving
          topic_id: topicId, // Add topic_id for saving
          parent_bullet: parentBulletKey, // Add parent bullet for layer 2 tracking
          layer: depth + 1, // Pass the layer based on expansion depth
        }),
      });

      if (!res.ok) {
        console.error("❌ HTTP error:", res.status, res.statusText);
        return;
      }

      const data = await res.json();
      console.log("📥 Backend sub-bullet expansion response:", data);

      if (data.error) {
        console.error("Error expanding sub-bullet:", data.error);
      } else {
        console.log("✅ Sub-bullet expansion result received:", data);
        // Store the sub-expansion result in the nested structure
        const subBulletKey = `${parentBulletKey}_sub_${subBullet.slice(0, 30)}`;
        setExpandedBullets(prev => {
          const updated = { ...prev };
          
          // Ensure the parent expansion exists
          if (updated[parentBulletKey]) {
            if (!updated[parentBulletKey].subExpansions) {
              updated[parentBulletKey].subExpansions = {};
            }
            updated[parentBulletKey].subExpansions![subBulletKey] = {
              expansion: data,
              subExpansions: {}
            };
          }
          
          return updated;
        });
      }
    } catch (error) {
      console.error("Failed to expand sub-bullet:", error);
    }
  };

  // Function to generate a consistent bullet key (must match backend logic)
  const generateBulletKey = (bulletPoint: string): string => {
    // Remove markdown formatting and limit length (match backend logic)
    const cleanBullet = bulletPoint.replace(/^[-*+]\s*/, '').trim();
    return cleanBullet.slice(0, 80); // Use first 80 chars as key
  };
  
  // Function to load saved bullet point expansions
  const loadSavedExpansions = (topicsData: TopicResponse) => {
    console.log("🔄 Loading saved expansions from topics data");
    const newExpandedBullets: Record<string, BulletExpansion> = {};
    
    Object.entries(topicsData.topics).forEach(([topicId, topic]) => {
      const bulletExpansions = topic.bullet_expansions;
      if (bulletExpansions) {
        console.log(`📂 Found saved expansions for topic ${topicId}:`, bulletExpansions);
        
        Object.entries(bulletExpansions).forEach(([bulletKey, expansionData]) => {
          const originalBullet = expansionData.original_bullet || bulletKey;
          const frontendKey = `${topicId}_${generateBulletKey(originalBullet)}`;
          
          console.log(`🔑 Loading layer 1 expansion: backend key '${bulletKey}' -> frontend key '${frontendKey}'`);
          
          // Load the main expansion
          newExpandedBullets[frontendKey] = {
            expansion: {
              original_bullet: originalBullet,
              expanded_bullets: expansionData.expanded_bullets,
              topic_heading: expansionData.topic_heading,
              chunks_used: expansionData.chunks_used
            },
            subExpansions: {}
          };
          
          // Load layer 2 sub-expansions if they exist
          if (expansionData.sub_expansions) {
            console.log(`🔗 Loading layer 2 sub-expansions for '${frontendKey}':`, expansionData.sub_expansions);
            
            Object.entries(expansionData.sub_expansions).forEach(([subKey, subExpansionData]) => {
              const originalSubBullet = subExpansionData.original_bullet || subKey;
              const subFrontendKey = `${frontendKey}_sub_${originalSubBullet.slice(0, 30)}`;
              
              console.log(`🔑 Loading layer 2 expansion: backend key '${subKey}' -> frontend key '${subFrontendKey}'`);
              
              if (!newExpandedBullets[frontendKey].subExpansions) {
                newExpandedBullets[frontendKey].subExpansions = {};
              }
              
              newExpandedBullets[frontendKey].subExpansions![subFrontendKey] = {
                expansion: {
                  original_bullet: originalSubBullet,
                  expanded_bullets: subExpansionData.expanded_bullets,
                  topic_heading: subExpansionData.topic_heading,
                  chunks_used: subExpansionData.chunks_used
                },
                subExpansions: {}
              };
            });
          }
        });
      }
    });
    
    console.log("✅ Loaded saved expansions:", newExpandedBullets);
    setExpandedBullets(newExpandedBullets);
  };

  const renderDebugResult = (topicId: string) => {
    const debugResult = topics?.topics[topicId]?.debugResult;
    console.log("🎨 Rendering debug result for topic:", topicId, debugResult);
    
    if (!debugResult) {
      console.log("❌ No debug result to render for topic:", topicId);
      return null;
    }

    console.log("✅ Rendering debug result:", debugResult);
    return (
      <div style={{ 
        marginTop: "1rem", 
        padding: "1rem", 
        border: "1px solid #ccc",
        borderRadius: "8px",
        background: "rgba(255, 255, 255, 0.02)"
      }}>
        <h4 style={{ margin: "0 0 1rem 0", color: "#fff" }}>Debugging Result:</h4>
        <p><strong>Bullet Point:</strong> {debugResult.bullet_point}</p>
        
        <div style={{ marginBottom: "1rem" }}>
          <strong>Top 5 Most Similar Chunks:</strong>
          <div style={{ marginTop: "0.5rem" }}>
            {debugResult.top_similar_chunks && debugResult.top_similar_chunks.map((item, idx) => (
              <div key={idx} style={{ 
                marginBottom: "0.8rem", 
                padding: "0.8rem", 
                background: idx === 0 ? "rgba(185, 255, 128, 0.1)" : "rgba(255, 255, 255, 0.05)",
                borderRadius: "6px",
                border: idx === 0 ? "1px solid rgba(185, 255, 128, 0.3)" : "1px solid rgba(255, 255, 255, 0.1)"
              }}>
                <div style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center",
                  marginBottom: "0.5rem"
                }}>
                  <strong style={{ color: idx === 0 ? "hsl(185, 100%, 70%)" : "#ccc" }}>
                    #{idx + 1} {idx === 0 ? "(Most Similar)" : ""}
                  </strong>
                  <span style={{ 
                    color: idx === 0 ? "hsl(185, 100%, 70%)" : "#999",
                    fontWeight: "bold"
                  }}>
                    {item.similarity.toFixed(3)}
                  </span>
                </div>
                <p style={{ 
                  margin: 0, 
                  color: "#ddd", 
                  fontSize: "0.9rem",
                  lineHeight: "1.4"
                }}>
                  {item.chunk}
                </p>
              </div>
            ))}
          </div>
        </div>

        <p><strong>Similarity to Current Topic:</strong> {debugResult.similarity_to_current_topic.toFixed(3)}</p>
        
        <div>
          <h5 style={{ margin: "1rem 0 0.5rem 0" }}>Topic Similarities:</h5>
          <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
            {debugResult.topic_similarities &&
              Object.entries(debugResult.topic_similarities)
                .sort(([,a], [,b]) => b - a) // Sort by similarity descending
                .map(([title, similarity]) => (
                  <li key={title} style={{ marginBottom: "0.3rem" }}>
                    {title}: <strong>{similarity.toFixed(3)}</strong>
                  </li>
                ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderSubBullets = (
    subBullets: string[], 
    parentBulletKey: string, 
    topicId: string, 
    subExpansions: NestedExpansions = {},
    depth: number = 1
  ) => {
    return (
      <ul style={{
        margin: "0.5rem 0 0 0",
        paddingLeft: "1.5rem",
        listStyleType: depth === 1 ? "circle" : "square",
        color: "#ddd"
      }}>
        {subBullets.map((subBullet: string) => {
          const cleanedSubBullet = subBullet.replace(/^[-*+]\s*/, '').trim();
          const subBulletKey = `${parentBulletKey}_sub_${subBullet.slice(0, 30)}`;
          const subExpansion = subExpansions[subBulletKey];
          
          return (
            <li 
              key={subBulletKey}
              style={{ 
                marginBottom: "0.5rem",
                fontSize: "inherit",
                lineHeight: "inherit",
                cursor: depth < 2 ? "pointer" : "default", // Only clickable if under depth limit
                opacity: depth < 2 ? 1 : 0.8 // Slightly fade out non-clickable items
              }}
              onClick={(e) => {
                e.stopPropagation(); // Prevent parent click
                if (depth < 2) {
                  if (isDeveloperMode) {
                    handleDebugBulletPoint(subBullet, topicId);
                  } else {
                    handleExpandSubBulletPoint(subBullet, topicId, parentBulletKey, depth);
                  }
                }
              }}
            >
              <div>
                <ReactMarkdown>{cleanedSubBullet}</ReactMarkdown>
                {subExpansion && subExpansion.expansion.expanded_bullets && (
                  renderSubBullets(
                    subExpansion.expansion.expanded_bullets,
                    subBulletKey,
                    topicId,
                    subExpansion.subExpansions || {},
                    depth + 1
                  )
                )}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  const renderBulletPoints = (bulletPoints: string[], topicId: string) => {
    return (
      <ul style={{ 
        margin: "0.5rem 0 0 0", 
        paddingLeft: "1.5rem",
        color: "#ddd",
        listStyleType: "disc"
      }}>
        {bulletPoints.map((point, idx) => {
          // Remove markdown list formatting (-, *, +) from the beginning of bullet points
          // since we're using HTML list styling
          const cleanedPoint = point.replace(/^[-*+]\s*/, '').trim();
          const bulletKey = `${topicId}_${generateBulletKey(point)}`;
          const isExpanded = expandedBullets[bulletKey];
          
          console.log(`🔍 Rendering bullet ${idx}: key='${bulletKey}', expanded=${!!isExpanded}`);
          
          return (
            <li 
              key={bulletKey} 
              style={{ marginBottom: "0.5rem", cursor: "pointer" }}
              onClick={() => {
                if (isDeveloperMode) {
                  handleDebugBulletPoint(point, topicId);
                } else {
                  handleExpandBulletPoint(point, topicId);
                }
              }}
            >
              <div>
                <ReactMarkdown>{cleanedPoint}</ReactMarkdown>
                {isExpanded && isExpanded.expansion.expanded_bullets && (
                  renderSubBullets(
                    isExpanded.expansion.expanded_bullets,
                    bulletKey,
                    topicId,
                    isExpanded.subExpansions || {},
                    1
                  )
                )}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <>
      {/* Single canvas for particle system - works for both connection screen and main UI */}
      <canvas
        ref={canvasRef}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          zIndex: -1,
          pointerEvents: "none",
        }}
      ></canvas>
      
      {(isInitializing || !isBackendReachable) ? (
        <ConnectionScreen />
      ) : (
        <>
          <ConnectionStatus />
          <div style={{ padding: "2rem", fontFamily: '"Outfit", sans-serif' }}>
            <div className="label fade-in" style={{ animationDelay: "0.2s" }}>
              MyStudyMate
            </div>
            <div
              className="glow-text fade-in"
              data-text="Smarter Studying Starts Here."
              style={{ animationDelay: "0.4s" }}
            >
              Smarter Studying Starts Here.
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.mp3,.wav,.txt,.m4a"
              style={{ display: "none" }}
            />

            <div
              ref={dropZoneRef}
              className={`drop-zone ${dragOver ? "drag-over" : ""}`}
              style={{
                marginTop: "4rem",
                ...(dragOver &&
                  activeHue !== null &&
                  ({
                    "--accent-hue": `${activeHue}`,
                  } as React.CSSProperties)),
                borderColor:
                  dragOver && activeHue !== null
                    ? `hsl(${activeHue}, 100%, 60%)`
                    : undefined,
              }}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                
                // Only update state if not already in drag state
                if (!dragOver) {
                  setDragOver(true);
                  
                  // Assign a random hue only on first drag entry
                  const randomHue =
                    ACCENT_HUES[Math.floor(Math.random() * ACCENT_HUES.length)];
                  setActiveHue(randomHue);
                  
                  // Apply transform only once
                  if (dropZoneRef.current) {
                    dropZoneRef.current.style.transform =
                      "rotateX(3deg) rotateY(0deg) scale(1.03)";
                  }
                }
              }}
              onDragLeave={() => {
                setDragOver(false);
                setActiveHue(null); // Reset for next hover

                if (dropZoneRef.current) {
                  dropZoneRef.current.style.transform = "";
                }

              }}
              onDrop={(e) => {
                setDragOver(false);
                setActiveHue(null); // Reset for next hover
                if (dropZoneRef.current) {
                  dropZoneRef.current.style.transform = "";
                }

                particleWorkerRef.current?.postMessage({ type: "explode" });
                handleDrop(e);
              }}
            >
              <div className="drop-zone-content">
                <div style={{
                  fontSize: "3rem",
                  marginBottom: "1.5rem",
                  opacity: dragOver ? 1 : 0.7,
                  transition: "all 0.3s ease",
                  transform: dragOver ? "scale(1.1)" : "scale(1)"
                }}>
                  {dragOver ? "📂" : "📁"}
                </div>
                
                <h3 style={{
                  margin: "0 0 1rem 0",
                  fontSize: "1.4rem",
                  fontWeight: "600",
                  color: "#fff",
                  opacity: dragOver ? 1 : 0.9,
                  transition: "opacity 0.3s ease"
                }}>
                  {dragOver ? "Drop your file here!" : "Upload Your Study Material"}
                </h3>
                
                <p style={{
                  margin: "0 0 1.5rem 0",
                  fontSize: "1rem",
                  color: "#ccc",
                  lineHeight: "1.5",
                  opacity: dragOver ? 0.8 : 0.7,
                  transition: "opacity 0.3s ease"
                }}>
                  {dragOver 
                    ? "Release to start processing..." 
                    : "Drag & drop your file here or click to browse"
                  }
                </p>
                
                <div style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.5rem",
                  justifyContent: "center",
                  marginBottom: "1rem"
                }}>
                  {[".pdf", ".mp3", ".wav", ".txt", ".m4a"].map((ext) => (
                    <span key={ext} style={{
                      background: "rgba(255, 255, 255, 0.1)",
                      color: "#ddd",
                      padding: "0.3rem 0.8rem",
                      borderRadius: "20px",
                      fontSize: "0.8rem",
                      fontWeight: "500",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      opacity: dragOver ? 0.6 : 0.8,
                      transition: "opacity 0.3s ease"
                    }}>
                      {ext}
                    </span>
                  ))}
                </div>
                
                <div style={{
                  fontSize: "0.85rem",
                  color: "#999",
                  opacity: dragOver ? 0.6 : 0.8,
                  transition: "opacity 0.3s ease"
                }}>
                  💡 Supports PDFs, audio files, and text documents
                </div>
              </div>
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}

            <AnimatePresence
              onExitComplete={() => {
                setProgressBarExited(true);
              }}
            >
              {showProgressBar && (
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={
                    allowUnmount
                      ? { opacity: 0, height: 0, transition: { duration: 0.4 } }
                      : {} // prevents auto exit until we say so
                  }
                  transition={{ duration: 0.4 }}
                  style={{
                    overflow: "hidden", // Needed for smooth height animation
                    marginTop: "1rem",
                    paddingBottom: "60px", // 🔧 Give extra space for enhanced glow
                    paddingLeft: "30px", // ✅ Balanced horizontal space for wider bar
                    paddingRight: "30px", // ✅ Balanced horizontal space for wider bar
                  }}
                >
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4 }}
                  >
                    {status?.stage === "uploading"
                      ? "Uploading file..."
                      : status?.stage === "preprocessing"
                      ? "Preprocessing audio..."
                      : status?.stage === "transcribing" &&
                        typeof status.current === "number" &&
                        typeof status.total === "number"
                      ? `Transcribing chunk ${status.current} of ${status.total}…`
                      : status?.stage === "saving_output"
                      ? "Saving output..."
                      : isFinishing
                      ? "Finishing up…"
                      : "Beginning transcription…"}
                  </motion.p>

                  {/* Enhanced wrapper to allow glow overflow */}
                  <div
                    style={{
                      position: "relative",
                      overflow: "visible", // ✅ Let glow extend outside
                      padding: "20px clamp(20px, 5vw, 40px)", // ✅ Responsive padding that scales with viewport
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      width: "100%", // ✅ Ensure full width for centering
                      boxSizing: "border-box", // ✅ Include padding in width calculation
                    }}
                  >
                    <div className="neon-progress-wrapper">
                      <motion.div
                        className="neon-progress-core"
                        initial={{ width: "0%", opacity: 0 }}
                        animate={coreControls}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        style={{ position: "absolute", left: 0, top: 0 }}
                      />
                      <motion.div
                        className="neon-progress-glow"
                        initial={{ width: "0%", opacity: 0 }}
                        animate={glowControls}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        style={{ position: "absolute", left: 0, top: 0 }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {canShowTranscript && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                style={{ 
                  marginTop: "3rem",
                  background: "linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%)",
                  borderRadius: "16px",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  padding: "2rem",
                  backdropFilter: "blur(10px)"
                }}
              >
                {/* File Info Header */}
                <div style={{ 
                  marginBottom: "2rem",
                  background: "rgba(0, 0, 0, 0.3)",
                  borderRadius: "12px",
                  padding: "1.5rem",
                  border: "1px solid rgba(255, 255, 255, 0.1)"
                }}>
                  <div style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    gap: "1rem",
                    marginBottom: "1rem"
                  }}>
                    <div style={{
                      width: "40px",
                      height: "40px",
                      borderRadius: "50%",
                      background: "linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "1.2rem"
                    }}>
                      📄
                    </div>
                    <div>
                      <h3 style={{ 
                        margin: 0, 
                        color: "#fff",
                        fontSize: "1.2rem",
                        fontWeight: "600"
                      }}>
                        File Successfully Processed
                      </h3>
                      <p style={{ 
                        margin: "0.2rem 0 0 0", 
                        color: "#999",
                        fontSize: "0.9rem"
                      }}>
                        Ready for analysis and topic extraction
                      </p>
                    </div>
                  </div>
                  
                  <div style={{ 
                    display: "grid", 
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: "1rem"
                  }}>
                    <div style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      gap: "0.5rem",
                      color: "#ccc"
                    }}>
                      <span style={{ fontSize: "0.9rem" }}>📁</span>
                      <div>
                        <div style={{ fontSize: "0.8rem", color: "#999" }}>Filename</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: "500" }}>{response.filename}</div>
                      </div>
                    </div>
                    
                    <div style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      gap: "0.5rem",
                      color: "#ccc"
                    }}>
                      <span style={{ fontSize: "0.9rem" }}>🏷️</span>
                      <div>
                        <div style={{ fontSize: "0.8rem", color: "#999" }}>File Type</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: "500" }}>{response.filetype}</div>
                      </div>
                    </div>
                    
                    <div style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      gap: "0.5rem",
                      color: "#ccc"
                    }}>
                      <span style={{ fontSize: "0.9rem" }}>✅</span>
                      <div>
                        <div style={{ fontSize: "0.8rem", color: "#999" }}>Status</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: "500", color: "#4ade80" }}>{response.message}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Transcript Display */}
                <div style={{ marginBottom: "1rem" }}>
                  <div style={{
                    display: "flex", 
                    alignItems: "center", 
                    gap: "0.75rem",
                    marginBottom: "1rem"
                  }}>
                    <h2 style={{ 
                      margin: 0, 
                      fontSize: "1.3rem",
                      fontWeight: "600",
                      color: "#fff"
                    }}>
                      📄 Extracted Transcript
                    </h2>
                    <div style={{
                      background: "rgba(185, 255, 255, 0.1)",
                      color: "hsl(185, 100%, 70%)",
                      padding: "0.3rem 0.8rem",
                      borderRadius: "20px",
                      fontSize: "0.8rem",
                      fontWeight: "500",
                      border: "1px solid rgba(185, 255, 255, 0.2)"
                    }}>
                      {response.text ? `${Math.round(response.text.length / 1000)}k characters` : "0 characters"}
                    </div>
                  </div>
                  
                  <div style={{
                    background: "rgba(0, 0, 0, 0.4)",
                    borderRadius: "12px",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    overflow: "hidden"
                  }}>
                    <div style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "0.75rem 1rem",
                      borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem"
                    }}>
                      <div style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: "#ef4444"
                      }}></div>
                      <div style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: "#f59e0b"
                      }}></div>
                      <div style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: "#10b981"
                      }}></div>
                      <span style={{ 
                        marginLeft: "0.5rem", 
                        fontSize: "0.8rem", 
                        color: "#999",
                        fontFamily: "monospace"
                      }}>
                        transcript.txt
                      </span>
                    </div>
                    
                    <div style={{
                      maxHeight: "400px",
                      overflowY: "auto",
                      padding: "1.5rem",
                      lineHeight: "1.6"
                    }}>
                      <pre style={{
                        margin: 0,
                        fontFamily: "'Fira Code', 'Consolas', monospace",
                        fontSize: "0.9rem",
                        color: "#e5e5e5",
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word"
                      }}>
                        {response.text || "No transcript content available"}
                      </pre>
                    </div>
                  </div>
                  
                  <div style={{ 
                    marginTop: "0.75rem",
                    fontSize: "0.8rem", 
                    color: "#888",
                    textAlign: "center"
                  }}>
                    💡 This transcript will be segmented and analyzed for key topics below
                  </div>
                </div>
              </motion.div>
            )}

            {canShowTranscript && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                style={{ 
                  marginTop: "2rem", 
                  display: "flex", 
                  gap: "1rem",
                  flexWrap: "wrap"
                }}
              >
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleProcessChunks}
                  disabled={!!processedChunks}
                  style={{
                    ...buttonStyle,
                    flex: "1",
                    minWidth: "250px",
                    padding: "1rem 1.5rem",
                    fontSize: "1rem",
                    fontWeight: "600",
                    background: processedChunks 
                      ? "linear-gradient(135deg, #10b981, #059669)"
                      : "linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))",
                    opacity: processedChunks ? 0.8 : 1,
                    cursor: processedChunks ? "not-allowed" : "pointer",
                    position: "relative",
                    overflow: "hidden"
                  }}
                >
                  <div style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    gap: "0.75rem",
                    justifyContent: "center"
                  }}>
                    <span style={{ fontSize: "1.1rem" }}>
                      {processedChunks ? "✅" : "🔧"}
                    </span>
                    <span>
                      {processedChunks
                        ? "Transcript Segmented ✔"
                        : "Segment & Optimize Transcript"}
                    </span>
                  </div>
                  {!processedChunks && (
                    <div style={{
                      position: "absolute",
                      top: 0,
                      left: "-100%",
                      width: "100%",
                      height: "100%",
                      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
                      animation: "shimmer 2s infinite"
                    }} />
                  )}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleGenerateHeadings}
                  disabled={!processedChunks || generatingHeadings}
                  style={{
                    ...buttonStyle,
                    flex: "1",
                    minWidth: "250px",
                    padding: "1rem 1.5rem",
                    fontSize: "1rem",
                    fontWeight: "600",
                    background: !processedChunks || generatingHeadings 
                      ? "linear-gradient(135deg, #6b7280, #4b5563)"
                      : "linear-gradient(135deg, hsl(315, 100%, 60%), hsl(330, 100%, 70%))",
                    opacity: !processedChunks || generatingHeadings ? 0.6 : 1,
                    cursor: !processedChunks || generatingHeadings ? "not-allowed" : "pointer",
                    position: "relative",
                    overflow: "hidden"
                  }}
                >
                  <div style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    gap: "0.75rem",
                    justifyContent: "center"
                  }}>
                    <span style={{ fontSize: "1.1rem" }}>
                      {generatingHeadings ? "⏳" : "🧠"}
                    </span>
                    <span>
                      {generatingHeadings
                        ? "Generating Topics..."
                        : "Generate Topics with AI"}
                    </span>
                  </div>
                  {processedChunks && !generatingHeadings && (
                    <div style={{
                      position: "absolute",
                      top: 0,
                      left: "-100%",
                      width: "100%",
                      height: "100%",
                      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
                      animation: "shimmer 2s infinite"
                    }} />
                  )}
                </motion.button>
              </motion.div>
            )}

            {topics && (
              <div style={{ marginTop: "2rem" }}>
                <h2>📊 Generated Topics</h2>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: "2rem" }}
                >
                  {Object.entries(topics.topics).map(([topicId, topic]) => (
                    <div key={topicId} style={{ 
                      background: "rgba(255, 255, 255, 0.05)", 
                      padding: "1.5rem", 
                      borderRadius: "12px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      textAlign: "left"
                    }}>
                      <h3 style={{ 
                        margin: "0 0 1rem 0", 
                        color: "#fff",
                        fontSize: "1.4rem"
                      }}>
                        {topic.heading}
                      </h3>
                      
                      {topic.concepts && topic.concepts.length > 0 && (
                        <div style={{ marginBottom: "1rem" }}>
                          <strong style={{ color: "#ccc", fontSize: "0.9rem" }}>
                            Key Concepts:
                          </strong>
                          <div style={{ 
                            display: "flex", 
                            flexWrap: "wrap", 
                            gap: "0.5rem", 
                            marginTop: "0.5rem" 
                          }}>
                            {topic.concepts.map((concept, idx) => (
                              <span key={idx} style={{
                                background: "rgba(185, 100%, 50%, 0.2)",
                                color: "hsl(185, 100%, 70%)",
                                padding: "0.3rem 0.8rem",
                                borderRadius: "20px",
                                fontSize: "0.85rem",
                                border: "1px solid rgba(185, 100%, 50%, 0.3)"
                              }}>
                                {concept}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div style={{ 
                        marginBottom: "1rem",
                        background: "rgba(255, 255, 255, 0.03)",
                        padding: "1rem",
                        borderRadius: "8px",
                        border: "1px solid rgba(255, 255, 255, 0.1)"
                      }}>
                        <strong style={{ color: "#ccc", fontSize: "0.9rem" }}>
                          Summary:
                        </strong>
                        <p style={{ 
                          margin: "0.5rem 0 0 0", 
                          color: topic.summary ? "#ddd" : "#888",
                          lineHeight: "1.5",
                          fontSize: "0.95rem",
                          fontStyle: topic.summary ? "normal" : "italic"
                        }}>
                          {topic.summary || "Summary not available for this topic."}
                        </p>
                      </div>
                      
                      <div style={{ 
                        display: "flex", 
                        gap: "1rem", 
                        fontSize: "0.8rem", 
                        color: "#999" 
                      }}>
                        <span>{topic.stats.num_chunks} chunks</span>
                        <span>Avg: {Math.round(topic.stats.mean_size)} words</span>
                      </div>

                      {/* Expand/Collapse buttons */}
                      <div style={{ 
                        marginTop: "1rem", 
                        display: "flex", 
                        flexDirection: "column", 
                        gap: "0.5rem" 
                      }}>
                        <button
                          onClick={() => handleExpandCluster(topicId)}
                          style={{
                            ...buttonStyle,
                            background: "hsl(185, 100%, 50%)",
                          }}
                        >
                          {topic.bullet_points
                            ? "Regenerate Insights"
                            : "Expand Cluster for More Insights"}
                        </button>
                      </div>

                      {/* Bullet points section */}
                      {topic.bullet_points && topic.bullet_points.length > 0 && (
                        <div style={{ 
                          marginTop: "1rem", 
                          padding: "1rem", 
                          background: "rgba(255, 255, 255, 0.04)", 
                          borderRadius: "8px",
                          border: "1px solid rgba(255, 255, 255, 0.1)"
                        }}>
                          <strong style={{ color: "#ccc", fontSize: "0.9rem" }}>
                            Key Bullet Points:
                          </strong>
                          {renderBulletPoints(topic.bullet_points, topicId)}
                        </div>
                      )}

                      {/* Debugging result section */}
                      {renderDebugResult(topicId)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Developer Mode Toggle */}
            <div style={{ 
              position: "fixed", 
              top: "1rem", 
              right: "1rem", 
              zIndex: 1000,
              background: "rgba(0, 0, 0, 0.8)",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "1px solid rgba(255, 255, 255, 0.2)"
            }}>
              <label style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: "0.5rem", 
                color: "#fff",
                fontSize: "0.9rem",
                cursor: "pointer"
              }}>
                <input
                  type="checkbox"
                  checked={isDeveloperMode}
                  onChange={(e) => setIsDeveloperMode(e.target.checked)}
                  style={{ margin: 0 }}
                />
                Developer Mode
              </label>
              <div style={{ 
                fontSize: "0.75rem", 
                color: "#999", 
                marginTop: "0.2rem" 
              }}>
                {isDeveloperMode ? "🔧 Click bullets to debug" : "📖 Click bullets to expand"}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export default App;
