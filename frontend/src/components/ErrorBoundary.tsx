import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      errorMessage: "",
    };
  }

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      errorMessage: error.message || "An unexpected error occurred.",
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("[ErrorBoundary] Caught render error:", error, errorInfo);
  }

  private reloadPage = (): void => {
    window.location.reload();
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "grid",
            placeItems: "center",
            backgroundColor: "#0b1220",
            color: "#e5e7eb",
            padding: "1.5rem",
            fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "36rem",
              border: "1px solid #1f2937",
              borderRadius: "0.75rem",
              backgroundColor: "#111827",
              padding: "1.25rem",
              boxShadow: "0 10px 30px rgba(0, 0, 0, 0.35)",
            }}
          >
            <h1 style={{ margin: "0 0 0.5rem", fontSize: "1.25rem", fontWeight: 600 }}>
              Something went wrong
            </h1>
            <p style={{ margin: "0 0 0.75rem", color: "#9ca3af" }}>
              The app hit an unexpected error while rendering.
            </p>
            <pre
              style={{
                margin: "0 0 1rem",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                backgroundColor: "#030712",
                border: "1px solid #1f2937",
                color: "#fca5a5",
                fontSize: "0.85rem",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {this.state.errorMessage}
            </pre>
            <button
              type="button"
              onClick={this.reloadPage}
              style={{
                border: "1px solid #374151",
                backgroundColor: "#1f2937",
                color: "#f9fafb",
                padding: "0.55rem 0.9rem",
                borderRadius: "0.5rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;