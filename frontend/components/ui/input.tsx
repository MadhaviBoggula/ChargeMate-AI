
import { useId } from "react";
import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export default function Input({
  label,
  error,
  helperText,
  id,
  className = "",
  ...props
}: InputProps) {
  const generatedId = useId();
  const inputId = id || props.name || generatedId;

  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-semibold text-slate-700"
        >
          {label}
        </label>
      )}

      <input
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={
          error
            ? `${inputId}-error`
            : helperText
              ? `${inputId}-helper`
              : undefined
        }
        className={[
          "w-full rounded-xl border bg-white px-4 py-3 text-sm text-slate-800",
          "placeholder:text-slate-400",
          "outline-none transition-all duration-200",
          "focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10",
          error
            ? "border-red-400 focus:border-red-500 focus:ring-red-500/10"
            : "border-slate-200",
          "disabled:cursor-not-allowed disabled:bg-slate-100",
          className,
        ].join(" ")}
        {...props}
      />

      {error && (
        <p id={`${inputId}-error`} className="text-xs text-red-600">
          {error}
        </p>
      )}

      {!error && helperText && (
        <p id={`${inputId}-helper`} className="text-xs text-slate-500">
          {helperText}
        </p>
      )}
    </div>
  );
}
