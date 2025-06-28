import { useState } from "react";
import "./App.css";
import { useEffect, useRef } from "react";
import VanillaTilt from "vanilla-tilt";
import { motion, AnimatePresence, useAnimation } from "framer-motion";

const ACCENT_HUES = [185, 315, 35]; // cyan, pink, peach

type UploadResponse = {
  filename: string;
  filetype: string;
  message: string;
  text?: string;
  transcription_file?: string;
};

type TopicResponse = {
  num_chunks: number;
  num_topics: number;
  total_tokens_used: number;
  topics: {
    [key: string]: {
      concepts: string[];
      heading: string;
      summary: string;
      keywords: string[];
      examples: string[];
      stats: {
        num_chunks: number;
        min_size: number;
        mean_size: number;
        max_size: number;
      };
      bullet_points?: string[]; // Added bullet_points property
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
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dropZoneRef = useRef<HTMLDivElement | null>(null);
  const [showProgressBar, setShowProgressBar] = useState(false);
  const [allowUnmount, setAllowUnmount] = useState(false);
  const [progressBarExited, setProgressBarExited] = useState(false);
  const [processedChunks, setProcessedChunks] = useState<{
    num_chunks: number;
    total_words: number;
  } | null>(null);
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setResponse(null);
      setTopics(null);
    }
  };

  const handleProcessChunks = async () => {
    if (!response?.text || !response.filename) return;

    setError(null);
    try {
      const res = await fetch("http://localhost:8000/process-chunks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: response.text,
          filename: response.filename,
        }),
      });

      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setProcessedChunks({
          num_chunks: data.num_chunks,
          total_words: data.total_words,
        });
      }
    } catch {
      setError("Failed to process chunks.");
    }
  };

  const handleGenerateHeadings = async () => {
    if (!response?.filename || !processedChunks) return;

    setGeneratingHeadings(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/generate-headings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ filename: response.filename }),
      });

      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setTopics(data);
      }
    } catch {
      setError("Failed to generate headings.");
    } finally {
      setGeneratingHeadings(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length === 0) return;

    if (droppedFiles.length > 1) {
      setError("Please upload only one file at a time.");
      return;
    }

    if (droppedFiles && droppedFiles.length > 0) {
      const file = droppedFiles[0];
      setFile(file);
      setResponse(null);
      setTopics(null);

      // Immediately upload the file
      const formData = new FormData();
      formData.append("file", file);

      setLoading(true);
      setError(null);

      fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.error) {
            setError(data.error);
            setResponse(null);
          } else {
            setJobId(data.job_id);

            const evt = new EventSource(
              `http://localhost:8000/progress/${data.job_id}`
            );
            evt.onmessage = (event) => {
              const parsed = JSON.parse(event.data);
              setStatus(parsed);

              // Once done, set final result into response state
              if (parsed.stage === "done" && parsed.result) {
                setResponse(parsed.result);
                if (parsed.result.topics) {
                  setTopics({ ...parsed.result, topics: parsed.result.topics });
                }
              }

              // Auto-close when finished
              if (["done", "error"].includes(parsed.stage)) {
                evt.close();
              }
            };
            evt.onerror = () => {
              evt.close();
              setError("Lost connection to server.");
            };
          }
        })
        .catch(() => {
          setError("Upload failed. Try again.");
        })
        .finally(() => {
          setLoading(false);
        });
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
    const canvas = document.getElementById("canvas") as HTMLCanvasElement;

    if (status?.stage === "transcribing") {
      setShowProgressBar(true);
      setAllowUnmount(false);
      setProgressBarExited(false);
    }

    if (status?.stage === "done") {
      coreControls.start({
        width: "100%",
        opacity: 1, // just in case
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

    if (
      status?.stage === "transcribing" &&
      typeof status.current === "number" &&
      typeof status.total === "number"
    ) {
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
      const res = await fetch("http://localhost:8000/expand-cluster", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: response.filename,
          cluster_id: clusterId,
        }),
      });

      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        console.log("Received bullet points:", data.cluster.bullet_points);
        // Update the specific topic with the expanded cluster data
        setTopics((prevTopics) => {
          if (!prevTopics) return prevTopics;

          const updatedTopics = { ...prevTopics.topics };
          updatedTopics[clusterId] = {
            ...updatedTopics[clusterId],
            bullet_points: data.cluster.bullet_points,
          };

          return { ...prevTopics, topics: updatedTopics };
        });
      }
    } catch {
      setError("Failed to expand cluster.");
    }
  };

  return (
    <>
      <canvas
        id="canvas"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          zIndex: -1,
          pointerEvents: "none",
        }}
      ></canvas>
      <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
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
            setDragOver(true);

            // Only assign a hue if not already set
            if (activeHue === null) {
              const randomHue =
                ACCENT_HUES[Math.floor(Math.random() * ACCENT_HUES.length)];
              setActiveHue(randomHue);
            }

            if (dropZoneRef.current) {
              dropZoneRef.current.style.transform =
                "rotateX(3deg) rotateY(0deg) scale(1.03)";
            }
            particleWorkerRef.current?.postMessage({
              type: "boost",
              value: true,
            });
            console.log("Boost activated");
          }}
          onDragLeave={() => {
            setDragOver(false);
            setActiveHue(null); // Reset for next hover

            if (dropZoneRef.current) {
              dropZoneRef.current.style.transform = "";
            }
            particleWorkerRef.current?.postMessage({
              type: "boost",
              value: false,
            });
            console.log("Boost deactivated");
          }}
          onDrop={(e) => {
            setDragOver(false);
            setActiveHue(null); // Reset for next hover
            if (dropZoneRef.current) {
              dropZoneRef.current.style.transform = "";
            }
            particleWorkerRef.current?.postMessage({
              type: "boost",
              value: false,
            });
            particleWorkerRef.current?.postMessage({ type: "explode" });
            handleDrop(e);
          }}
        >
          <p>Drop your file here or click to upload</p>
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
                paddingBottom: "40px", // 🔧 Give space for glow
              }}
            >
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                {status?.stage === "transcribing" &&
                typeof status.current === "number" &&
                typeof status.total === "number"
                  ? `Transcribing chunk ${status.current} of ${status.total}…`
                  : isFinishing
                  ? "Finishing up…"
                  : "Beginning transcription…"}
              </motion.p>

              {/* NEW WRAPPER to allow overflow */}
              <div
                style={{
                  position: "relative",
                  overflow: "visible", // ✅ Let glow extend outside
                  padding: "0 32px", // ✅ Prevent horizontal clipping
                  display: "flex",
                  justifyContent: "center",
                }}
              >
                <div className="neon-progress-wrapper">
                  <motion.div
                    className="neon-progress-core"
                    initial={{ width: "0%", opacity: 0 }}
                    animate={coreControls}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                  <motion.div
                    className="neon-progress-glow"
                    initial={{ width: "0%", opacity: 0 }}
                    animate={glowControls}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {canShowTranscript && (
          <div style={{ marginTop: "2rem" }}>
            <p>
              <strong>File Uploaded:</strong> {response.filename}
            </p>
            <p>
              <strong>Type:</strong> {response.filetype}
            </p>
            <p>
              <strong>Status:</strong> {response.message}
            </p>
          </div>
        )}

        {canShowTranscript && (
          <div style={{ marginTop: "2rem" }}>
            <h2>📄 Extracted Text</h2>
            <textarea
              readOnly
              value={response.text}
              style={{
                width: "100%",
                height: "300px",
                padding: "1rem",
                fontFamily: "monospace",
                whiteSpace: "pre-wrap",
              }}
            />
          </div>
        )}

        {canShowTranscript && (
          <div style={{ marginTop: "1rem", display: "flex", gap: "1rem" }}>
            <button
              onClick={handleProcessChunks}
              disabled={!!processedChunks}
              style={{
                ...buttonStyle,
                opacity: processedChunks ? 0.6 : 1,
                cursor: processedChunks ? "not-allowed" : "pointer",
              }}
            >
              {processedChunks
                ? "Chunks Processed ✔"
                : "Segment & Optimize Transcript"}
            </button>

            <button
              onClick={handleGenerateHeadings}
              disabled={!processedChunks || generatingHeadings}
              style={{
                ...buttonStyle,
                opacity: !processedChunks || generatingHeadings ? 0.6 : 1,
                cursor:
                  !processedChunks || generatingHeadings
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              {generatingHeadings
                ? "Generating Headings..."
                : "Generate Headings with BERTopic"}
            </button>
          </div>
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
                      <ul style={{ 
                        margin: "0.5rem 0 0 0", 
                        paddingLeft: "1.5rem",
                        color: "#ddd",
                        listStyleType: "disc"
                      }}>
                        {topic.bullet_points.map((point, idx) => (
                          <li key={idx} style={{ marginBottom: "0.5rem" }}>
                            {point.replace(/^\s*-\s*/, '')}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default App;
