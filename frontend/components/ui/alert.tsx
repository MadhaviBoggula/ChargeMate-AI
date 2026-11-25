
import type { HTMLAttributes } from "react";

type AlertVariant = "success" | "error" | "warning" | "info";

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
}

const styles: Record<AlertVariant, string> = {
  success: "border-green-200 bg-green-50 text-green-800",
  error: "border-red-200 bg-red-50 text-red-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  info: "border-blue-200 bg-blue-50 text-blue-800",
};

export default function Alert({
  variant = "info",
  title,
  children,
  className = "",
  ...props
}: AlertProps) {
  return (
    <div
      role="alert"
      className={[
        "rounded-xl border px-4 py-3 text-sm",
        styles[variant],
        className,
      ].join(" ")}
      {...props}
    >
      {title && <p className="mb-1 font-semibold">{title}</p>}
      <div>{children}</div>
    </div>
  );
}
