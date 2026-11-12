
interface LoaderProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  fullScreen?: boolean;
}

export default function Loader({
  size = "md",
  text,
  fullScreen = false,
}: LoaderProps) {
  const sizes = {
    sm: "h-5 w-5 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div
      className={`flex items-center justify-center gap-3 ${
        fullScreen ? "min-h-screen" : "py-4"
      }`}
      role="status"
      aria-live="polite"
    >
      <div
        className={`animate-spin rounded-full border-blue-100 border-t-blue-600 ${sizes[size]}`}
      />

      {text && (
        <span className="text-sm font-medium text-slate-600">
          {text}
        </span>
      )}

      <span className="sr-only">{text || "Loading..."}</span>
    </div>
  );
}
