

type BrandLogoProps = {
  light?: boolean;
  compact?: boolean;
};

export default function BrandLogo({
  light = false,
  compact = false,
}: BrandLogoProps) {
  return (
    <div className="flex items-center gap-3">
      <svg
        viewBox="0 0 48 48"
        className="h-11 w-11 shrink-0"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="ChargeMate AI logo"
        role="img"
      >
        {/* Blue and green lightning bolt */}
        <path
          d="M29 3L8 27H21L17 45L40 17H26L29 3Z"
          fill="#168BEB"
        />
        <path
          d="M26 17H40L17 45L21 27H29L26 17Z"
          fill="#20B96B"
        />
      </svg>

      {!compact && (
        <div className="leading-tight">
          <div
            className={`text-xl font-extrabold tracking-tight ${
              light ? "text-white" : "text-[#10294B]"
            }`}
          >
            ChargeMate
          </div>

          <div className="mt-1 text-[10px] font-bold tracking-[0.24em] text-[#20A875]">
            AI · SMART EV CHARGING
          </div>
        </div>
      )}
    </div>
  );
}
