

"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import BrandLogo from "../../components/brand-logo";

type Station = {
  id: number;
  name: string;
  location: string;
  address: string;
  connectors: string[];
  chargerType: "DC" | "AC";
  power: number;
  speed: "Fast" | "Standard";
  available: number;
  total: number;
  price: number;
  status: "Available" | "Limited" | "Full";
  description: string;
};

type FilterOption = {
  label: string;
  value: string;
  detail: string;
  icon: string;
};

const stations: Station[] = [
  {
    id: 1,
    name: "ChargeMate Central",
    location: "Benz Circle",
    address: "Benz Circle, Vijayawada, Andhra Pradesh",
    connectors: ["CCS2", "Type 2"],
    chargerType: "DC",
    power: 60,
    speed: "Fast",
    available: 5,
    total: 8,
    price: 18,
    status: "Available",
    description:
      "A convenient charging destination with fast charging support and multiple connector options.",
  },
  {
    id: 2,
    name: "Green Energy Hub",
    location: "MG Road",
    address: "MG Road, Vijayawada, Andhra Pradesh",
    connectors: ["Type 2"],
    chargerType: "AC",
    power: 22,
    speed: "Standard",
    available: 3,
    total: 6,
    price: 15,
    status: "Available",
    description:
      "An everyday charging option designed for convenient standard charging.",
  },
  {
    id: 3,
    name: "Urban Charge Point",
    location: "Auto Nagar",
    address: "Auto Nagar, Vijayawada, Andhra Pradesh",
    connectors: ["CCS2", "CHAdeMO"],
    chargerType: "DC",
    power: 90,
    speed: "Fast",
    available: 2,
    total: 5,
    price: 20,
    status: "Limited",
    description:
      "A high-power charging option with DC charging support.",
  },
  {
    id: 4,
    name: "EcoDrive Station",
    location: "Poranki",
    address: "Poranki, Vijayawada, Andhra Pradesh",
    connectors: ["Type 2", "CCS2"],
    chargerType: "AC",
    power: 30,
    speed: "Standard",
    available: 4,
    total: 7,
    price: 16,
    status: "Available",
    description:
      "A practical charging option with multiple connector standards.",
  },
];

const connectorOptions: FilterOption[] = [
  {
    label: "All connectors",
    value: "All",
    detail: "Show every connector standard",
    icon: "layers",
  },
  {
    label: "CCS2",
    value: "CCS2",
    detail: "DC fast charging connector",
    icon: "plug",
  },
  {
    label: "Type 2",
    value: "Type 2",
    detail: "AC charging connector",
    icon: "cable",
  },
  {
    label: "CHAdeMO",
    value: "CHAdeMO",
    detail: "DC charging standard",
    icon: "zap",
  },
];

const chargerOptions: FilterOption[] = [
  {
    label: "All charger types",
    value: "All",
    detail: "Explore both AC and DC stations",
    icon: "layers",
  },
  {
    label: "AC charging",
    value: "AC",
    detail: "Suitable for standard charging",
    icon: "activity",
  },
  {
    label: "DC charging",
    value: "DC",
    detail: "Direct-current charging",
    icon: "bolt",
  },
];

const speedOptions: FilterOption[] = [
  {
    label: "All speeds",
    value: "All",
    detail: "Show every charging speed",
    icon: "gauge",
  },
  {
    label: "Fast charging",
    value: "Fast",
    detail: "Higher-power charging options",
    icon: "rocket",
  },
  {
    label: "Standard charging",
    value: "Standard",
    detail: "Everyday charging options",
    icon: "clock",
  },
];

const powerOptions: FilterOption[] = [
  {
    label: "Any power",
    value: "0",
    detail: "No minimum power requirement",
    icon: "sliders",
  },
  {
    label: "20 kW and above",
    value: "20",
    detail: "At least 20 kW output",
    icon: "battery",
  },
  {
    label: "50 kW and above",
    value: "50",
    detail: "At least 50 kW output",
    icon: "gauge",
  },
  {
    label: "80 kW and above",
    value: "80",
    detail: "High-power charging options",
    icon: "zap",
  },
];

const priceOptions: FilterOption[] = [
  {
    label: "Any price",
    value: "0",
    detail: "No maximum price limit",
    icon: "wallet",
  },
  {
    label: "Up to ₹15 / kWh",
    value: "15",
    detail: "Maximum ₹15 per kWh",
    icon: "coins",
  },
  {
    label: "Up to ₹16 / kWh",
    value: "16",
    detail: "Maximum ₹16 per kWh",
    icon: "badge",
  },
  {
    label: "Up to ₹18 / kWh",
    value: "18",
    detail: "Maximum ₹18 per kWh",
    icon: "receipt",
  },
  {
    label: "Up to ₹20 / kWh",
    value: "20",
    detail: "Maximum ₹20 per kWh",
    icon: "banknote",
  },
];

const statusOptions: FilterOption[] = [
  {
    label: "All statuses",
    value: "All",
    detail: "Show every station",
    icon: "layers",
  },
  {
    label: "Available",
    value: "Available",
    detail: "Stations with available slots",
    icon: "check",
  },
  {
    label: "Limited",
    value: "Limited",
    detail: "Stations with fewer available slots",
    icon: "alert",
  },
  {
    label: "Full",
    value: "Full",
    detail: "Stations with no available slots",
    icon: "ban",
  },
];

const vehicleOptions: FilterOption[] = [
  {
    label: "Any connector",
    value: "All",
    detail: "Do not filter by vehicle connector",
    icon: "car",
  },
  {
    label: "CCS2",
    value: "CCS2",
    detail: "Find stations supporting CCS2",
    icon: "plug",
  },
  {
    label: "Type 2",
    value: "Type 2",
    detail: "Find stations supporting Type 2",
    icon: "cable",
  },
  {
    label: "CHAdeMO",
    value: "CHAdeMO",
    detail: "Find stations supporting CHAdeMO",
    icon: "zap",
  },
];

function Icon({
  name,
  size = 20,
  className = "",
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "search":
      return (
        <svg {...common}>
          <circle cx="10.8" cy="10.8" r="6.8" />
          <path d="m16 16 4.5 4.5" />
        </svg>
      );
    case "chevron":
      return (
        <svg {...common}>
          <path d="m7 10 5 5 5-5" />
        </svg>
      );
    case "layers":
      return (
        <svg {...common}>
          <path d="m12 3 9 5-9 5-9-5 9-5Z" />
          <path d="m3 12 9 5 9-5" />
          <path d="m3 16 9 5 9-5" />
        </svg>
      );
    case "plug":
      return (
        <svg {...common}>
          <path d="M8 7v5a4 4 0 0 0 8 0V7" />
          <path d="M6 7h12M10 3v4m4-4v4M12 16v5" />
        </svg>
      );
    case "cable":
      return (
        <svg {...common}>
          <path d="M8 7V4m8 3V4M6 7h12v3a6 6 0 0 1-12 0V7Z" />
          <path d="M12 16v5m-3 0h6" />
        </svg>
      );
    case "zap":
      return (
        <svg {...common}>
          <path d="m13 2-9 12h7l-1 8 10-13h-7l0-7Z" />
        </svg>
      );
    case "bolt":
      return (
        <svg {...common}>
          <path d="M13 2 5 13h6l-1 9 9-12h-6l0-8Z" />
          <path d="M4 4h3M3 8h2" />
        </svg>
      );
    case "activity":
      return (
        <svg {...common}>
          <path d="M3 12h4l3-8 4 16 3-8h4" />
        </svg>
      );
    case "gauge":
      return (
        <svg {...common}>
          <path d="M4 17a9 9 0 1 1 16 0" />
          <path d="m12 13 4-4" />
          <path d="M7 17h10" />
        </svg>
      );
    case "rocket":
      return (
        <svg {...common}>
          <path d="M5 14c-2 1-2 5-2 5s4 0 5-2" />
          <path d="M8 13 5 10l5-5c3-3 8-3 11-3 0 3 0 8-3 11l-5 5-3-3" />
          <circle cx="15.5" cy="8.5" r="1.5" />
        </svg>
      );
    case "clock":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      );
    case "battery":
      return (
        <svg {...common}>
          <rect x="3" y="7" width="17" height="10" rx="2" />
          <path d="M20 10h2v4h-2M7 10v4m4-4v4" />
        </svg>
      );
    case "sliders":
      return (
        <svg {...common}>
          <path d="M4 6h16M4 12h16M4 18h16" />
          <circle cx="9" cy="6" r="2" fill="currentColor" />
          <circle cx="15" cy="12" r="2" fill="currentColor" />
          <circle cx="7" cy="18" r="2" fill="currentColor" />
        </svg>
      );
    case "wallet":
      return (
        <svg {...common}>
          <rect x="3" y="5" width="18" height="15" rx="3" />
          <path d="M3 9h18M16 14h2" />
        </svg>
      );
    case "coins":
      return (
        <svg {...common}>
          <ellipse cx="9" cy="7" rx="6" ry="3" />
          <path d="M3 7v5c0 1.7 2.7 3 6 3s6-1.3 6-3V7" />
          <path d="M15 10c3 0 6 1.3 6 3v4c0 1.7-2.7 3-6 3s-6-1.3-6-3" />
        </svg>
      );
    case "badge":
      return (
        <svg {...common}>
          <path d="M12 3 15 5l4 .5.5 4 2 3.5-2 3.5-.5 4-4 .5-3 2-3-2-4-.5-.5-4-2-3.5 2-3.5.5-4L9 5l3-2Z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case "receipt":
      return (
        <svg {...common}>
          <path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z" />
          <path d="M9 8h6M9 12h6M9 16h3" />
        </svg>
      );
    case "banknote":
      return (
        <svg {...common}>
          <rect x="2.5" y="5" width="19" height="14" rx="2" />
          <circle cx="12" cy="12" r="3" />
          <path d="M6 9h.01M18 15h.01" />
        </svg>
      );
    case "check":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="m8 12 2.5 2.5L16 9" />
        </svg>
      );
    case "alert":
      return (
        <svg {...common}>
          <path d="m12 3 10 18H2L12 3Z" />
          <path d="M12 9v5m0 3h.01" />
        </svg>
      );
    case "ban":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="m5.5 5.5 13 13" />
        </svg>
      );
    case "car":
      return (
        <svg {...common}>
          <path d="m5 11 2-5h10l2 5" />
          <path d="M3 11h18v7H3z" />
          <path d="M6 18v2m12-2v2M6 14h2m8 0h2" />
        </svg>
      );
    case "heart":
      return (
        <svg {...common}>
          <path d="M20.8 8.8c0 5-8.8 11-8.8 11s-8.8-6-8.8-11A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 8.8 2.8Z" />
        </svg>
      );
    case "pin":
      return (
        <svg {...common}>
          <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
          <circle cx="12" cy="10" r="2.5" />
        </svg>
      );
    case "arrow":
      return (
        <svg {...common}>
          <path d="M5 12h14m-6-6 6 6-6 6" />
        </svg>
      );
    case "close":
      return (
        <svg {...common}>
          <path d="m18 6-12 12M6 6l12 12" />
        </svg>
      );
    case "station":
      return (
        <svg {...common}>
          <rect x="5" y="3" width="12" height="18" rx="2" />
          <path d="M8 7h6v5H8zM17 8h2l2 3v6h-4M9 17h4" />
        </svg>
      );
    default:
      return null;
  }
}

function AdvancedFilter({
  label,
  value,
  options,
  onChange,
  icon,
}: {
  label: string;
  value: string;
  options: FilterOption[];
  onChange: (value: string) => void;
  icon: string;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const selected =
    options.find((option) => option.value === value) ?? options[0];

  const accents = [
    {
      icon: "bg-blue-100 text-blue-700",
      selected: "border-blue-300 bg-blue-50",
      dot: "bg-blue-600",
    },
    {
      icon: "bg-emerald-100 text-emerald-700",
      selected: "border-emerald-300 bg-emerald-50",
      dot: "bg-emerald-600",
    },
    {
      icon: "bg-violet-100 text-violet-700",
      selected: "border-violet-300 bg-violet-50",
      dot: "bg-violet-600",
    },
    {
      icon: "bg-orange-100 text-orange-700",
      selected: "border-orange-300 bg-orange-50",
      dot: "bg-orange-500",
    },
    {
      icon: "bg-cyan-100 text-cyan-700",
      selected: "border-cyan-300 bg-cyan-50",
      dot: "bg-cyan-600",
    },
  ];

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  return (
    <div
      ref={wrapperRef}
      className={`relative min-w-0 ${open ? "z-50" : "z-0"}`}
    >
      <label className="mb-2 flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.14em] text-slate-500">
        <Icon name={icon} size={16} className="text-blue-600" />
        {label}
      </label>

      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((previous) => !previous)}
        className={`group flex min-h-[82px] w-full items-center justify-between gap-3 rounded-2xl border-2 px-4 py-3 text-left transition-all duration-300 ${
          open
            ? "border-blue-500 bg-blue-50 shadow-lg shadow-blue-100 ring-4 ring-blue-100/70"
            : "border-slate-200 bg-white shadow-sm hover:border-blue-300 hover:bg-slate-50 hover:shadow-md"
        }`}
      >
        <span className="flex min-w-0 items-center gap-3">
          <span
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-all duration-300 ${
              open
                ? "bg-[#10294b] text-white shadow-md"
                : "bg-gradient-to-br from-blue-100 to-cyan-100 text-blue-700 group-hover:from-blue-200 group-hover:to-cyan-200"
            }`}
          >
            <Icon name={selected.icon} size={23} />
          </span>

          <span className="min-w-0">
            <span className="block truncate text-sm font-extrabold text-slate-800">
              {selected.label}
            </span>
            <span className="mt-1 block truncate text-xs text-slate-500">
              {selected.detail}
            </span>
            <span
              className={`mt-1.5 block text-[9px] font-extrabold uppercase tracking-[0.15em] ${
                open ? "text-blue-700" : "text-slate-400"
              }`}
            >
              {open ? "Options are open" : "Tap to choose"}
            </span>
          </span>
        </span>

        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all duration-300 ${
            open
              ? "rotate-180 bg-[#10294b] text-white"
              : "bg-slate-100 text-slate-600 group-hover:bg-blue-100 group-hover:text-blue-700"
          }`}
        >
          <Icon name="chevron" size={21} />
        </span>
      </button>

      {open && (
        <div
          id={listId}
          role="listbox"
          aria-label={label}
          className="absolute left-0 right-0 top-full z-[60] mt-3 min-w-[280px] overflow-hidden rounded-[26px] border border-slate-200 bg-white shadow-2xl shadow-slate-400/30 sm:min-w-[320px]"
        >
          <div className="relative overflow-hidden bg-gradient-to-r from-[#10294b] via-[#16446e] to-[#087c91] p-5 text-white">
            <div className="absolute -right-5 -top-10 h-32 w-32 rounded-full border border-white/15" />
            <div className="absolute -right-1 -top-5 h-20 w-20 rounded-full border border-white/15" />

            <div className="relative flex items-center justify-between gap-3">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-cyan-200">
                  CHARGEMATE AI
                </span>
                <h3 className="mt-2 text-lg font-extrabold">
                  Select {label}
                </h3>
                <p className="mt-1 text-xs text-blue-100">
                  Choose the option that suits you.
                </p>
              </div>

              <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/20 bg-white/10">
                <Icon name={icon} size={25} />
              </span>
            </div>

            <div className="relative mt-4 flex items-center justify-between">
              <span className="text-[10px] font-bold text-blue-100">
                AVAILABLE OPTIONS
              </span>
              <span className="rounded-full bg-white/15 px-3 py-1 text-[10px] font-extrabold text-white">
                {options.length} choices
              </span>
            </div>
          </div>

          <div className="max-h-[340px] space-y-2 overflow-y-auto bg-slate-50/80 p-3">
            {options.map((option, index) => {
              const isSelected = option.value === value;
              const accent = accents[index % accents.length];

              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                  }}
                  className={`group flex w-full items-center gap-3 rounded-2xl border-2 p-3 text-left transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${
                    isSelected
                      ? `${accent.selected} shadow-sm`
                      : "border-white bg-white hover:border-slate-200"
                  }`}
                >
                  <span
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl transition-transform duration-200 group-hover:scale-105 ${accent.icon}`}
                  >
                    <Icon name={option.icon} size={23} />
                  </span>

                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-extrabold text-slate-800">
                        {option.label}
                      </span>
                      {isSelected && (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-extrabold uppercase text-emerald-700">
                          Selected
                        </span>
                      )}
                    </span>
                    <span className="mt-1 block text-xs leading-5 text-slate-500">
                      {option.detail}
                    </span>
                  </span>

                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-all ${
                      isSelected
                        ? `${accent.dot} text-white`
                        : "border-2 border-slate-200 bg-white text-transparent group-hover:border-blue-300"
                    }`}
                  >
                    <Icon name="check" size={15} />
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 bg-white px-4 py-3">
            <span className="text-[10px] font-semibold text-slate-400">
              Selected: {selected.label}
            </span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full bg-[#10294b] px-4 py-2 text-xs font-bold text-white transition hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StationCard({
  station,
  favorite,
  onFavorite,
  onDetails,
}: {
  station: Station;
  favorite: boolean;
  onFavorite: () => void;
  onDetails: () => void;
}) {
  const statusStyles = {
    Available: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    Limited: "bg-amber-50 text-amber-700 ring-amber-200",
    Full: "bg-rose-50 text-rose-700 ring-rose-200",
  };

  return (
    <article className="group overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/60">
      <div className="relative overflow-hidden bg-gradient-to-br from-[#10294b] via-[#123c68] to-[#087c91] p-6 text-white">
        <div className="absolute -right-10 -top-14 h-40 w-40 rounded-full border border-white/10" />
        <div className="absolute -right-2 -top-7 h-28 w-28 rounded-full border border-white/10" />

        <div className="relative flex items-start justify-between gap-3">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.15em] text-cyan-100">
              <Icon name="station" size={13} />
              Charging station
            </span>

            <h3 className="mt-4 text-xl font-extrabold tracking-tight">
              {station.name}
            </h3>

            <p className="mt-2 flex items-center gap-2 text-sm text-blue-100">
              <Icon name="pin" size={15} />
              {station.location}, Vijayawada
            </p>
          </div>

          <button
            type="button"
            onClick={onFavorite}
            aria-label={
              favorite ? "Remove from favourites" : "Add to favourites"
            }
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border transition-all ${
              favorite
                ? "border-rose-300 bg-rose-500 text-white"
                : "border-white/20 bg-white/10 text-white hover:bg-white/20"
            }`}
          >
            <Icon name="heart" size={19} />
          </button>
        </div>

        <div className="relative mt-5 flex flex-wrap gap-2">
          {station.connectors.map((connector) => (
            <span
              key={connector}
              className="rounded-lg border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white"
            >
              {connector}
            </span>
          ))}

          <span className="rounded-lg border border-cyan-200/20 bg-cyan-300/15 px-3 py-1.5 text-xs font-semibold text-cyan-100">
            {station.chargerType} charger
          </span>
        </div>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-slate-50 p-3">
            <Icon name="battery" size={18} className="text-blue-600" />
            <p className="mt-2 text-lg font-extrabold text-slate-800">
              {station.available}/{station.total}
            </p>
            <p className="text-[10px] font-semibold text-slate-400">SLOTS</p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-3">
            <Icon name="zap" size={18} className="text-amber-500" />
            <p className="mt-2 text-lg font-extrabold text-slate-800">
              {station.power}
            </p>
            <p className="text-[10px] font-semibold text-slate-400">kW POWER</p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-3">
            <Icon name="wallet" size={18} className="text-emerald-600" />
            <p className="mt-2 text-lg font-extrabold text-slate-800">
              ₹{station.price}
            </p>
            <p className="text-[10px] font-semibold text-slate-400">PER kWh</p>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <span
            className={`rounded-full px-3 py-1.5 text-xs font-bold ring-1 ${statusStyles[station.status]}`}
          >
            {station.status}
          </span>

          <span className="text-xs font-semibold text-slate-500">
            {station.speed} charging
          </span>
        </div>

        <button
          type="button"
          onClick={onDetails}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#10294b] px-4 py-3 text-sm font-bold text-white transition-all hover:bg-blue-700"
        >
          Explore station details
          <Icon name="arrow" size={17} />
        </button>
      </div>
    </article>
  );
}

export default function StationsPage() {
  const [search, setSearch] = useState("");
  const [connector, setConnector] = useState("All");
  const [chargerType, setChargerType] = useState("All");
  const [speed, setSpeed] = useState("All");
  const [status, setStatus] = useState("All");
  const [maxPrice, setMaxPrice] = useState("0");
  const [minPower, setMinPower] = useState("0");
  const [vehicleConnector, setVehicleConnector] = useState("All");
  const [favorites, setFavorites] = useState<number[]>([]);
  const [showFavorites, setShowFavorites] = useState(false);
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);

  const filteredStations = useMemo(() => {
    return stations.filter((station) => {
      const searchMatch =
        station.name.toLowerCase().includes(search.toLowerCase()) ||
        station.location.toLowerCase().includes(search.toLowerCase()) ||
        station.address.toLowerCase().includes(search.toLowerCase());

      const connectorMatch =
        connector === "All" || station.connectors.includes(connector);

      const vehicleMatch =
        vehicleConnector === "All" ||
        station.connectors.includes(vehicleConnector);

      const chargerMatch =
        chargerType === "All" || station.chargerType === chargerType;

      const speedMatch = speed === "All" || station.speed === speed;

      const statusMatch = status === "All" || station.status === status;

      const priceMatch =
        maxPrice === "0" || station.price <= Number(maxPrice);

      const powerMatch =
        minPower === "0" || station.power >= Number(minPower);

      const favoriteMatch =
        !showFavorites || favorites.includes(station.id);

      return (
        searchMatch &&
        connectorMatch &&
        vehicleMatch &&
        chargerMatch &&
        speedMatch &&
        statusMatch &&
        priceMatch &&
        powerMatch &&
        favoriteMatch
      );
    });
  }, [
    search,
    connector,
    vehicleConnector,
    chargerType,
    speed,
    status,
    maxPrice,
    minPower,
    showFavorites,
    favorites,
  ]);

  const activeFilterCount = [
    connector !== "All",
    chargerType !== "All",
    speed !== "All",
    status !== "All",
    maxPrice !== "0",
    minPower !== "0",
    vehicleConnector !== "All",
  ].filter(Boolean).length;

  function resetFilters() {
    setSearch("");
    setConnector("All");
    setChargerType("All");
    setSpeed("All");
    setStatus("All");
    setMaxPrice("0");
    setMinPower("0");
    setVehicleConnector("All");
    setShowFavorites(false);
  }

  function toggleFavorite(id: number) {
    setFavorites((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id],
    );
  }

  return (
    <main className="min-h-screen bg-[#f5f9ff] text-slate-900">
      {/* Navigation */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <BrandLogo />

          <nav className="hidden items-center gap-9 md:flex">
            {[
              { label: "Home", href: "/" },
              { label: "Stations", href: "/stations" },
              { label: "Features", href: "/#features" },
              { label: "About", href: "/#about" },
            ].map((item) => (
              <a
                key={item.label}
                href={item.href}
                className={`group relative py-2 text-sm transition-colors duration-200 hover:font-bold hover:text-slate-950 ${
                  item.label === "Stations"
                    ? "font-bold text-slate-950"
                    : "font-semibold text-slate-600"
                }`}
              >
                {item.label}
                <span className="absolute -bottom-0.5 left-0 h-0.5 w-full origin-left scale-x-0 rounded-full bg-gradient-to-r from-blue-600 to-emerald-400 transition-transform duration-300 group-hover:scale-x-100" />
              </a>
            ))}
          </nav>

          <a
            href="/login"
            className="rounded-full border border-emerald-300 bg-white px-5 py-2.5 text-sm font-bold text-emerald-800 shadow-sm transition-all duration-300 hover:border-emerald-200 hover:bg-emerald-100 hover:text-emerald-900 hover:shadow-lg hover:shadow-emerald-100"
          >
            Sign In
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="relative isolate overflow-hidden bg-gradient-to-br from-[#10294b] via-[#123b68] to-[#087c91]">
        <div className="absolute -right-24 -top-28 h-96 w-96 rounded-full border border-white/10" />
        <div className="absolute -right-8 -top-12 h-64 w-64 rounded-full border border-white/10" />
        <div className="absolute -bottom-32 left-1/4 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-10 px-5 py-16 md:grid-cols-[1.3fr_0.7fr] md:py-20 lg:px-8">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.16em] text-cyan-100">
              <Icon name="zap" size={15} />
              Smarter EV charging discovery
            </span>

            <h1 className="mt-6 max-w-3xl text-4xl font-black leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
              Find your ideal
              <span className="block bg-gradient-to-r from-cyan-200 to-emerald-300 bg-clip-text text-transparent">
                charging station.
              </span>
            </h1>

            <p className="mt-5 max-w-xl text-base leading-8 text-blue-100 sm:text-lg">
              Discover charging options that match your vehicle, connector,
              charging speed and budget.
            </p>

            <div className="mt-7 flex flex-wrap gap-3 text-xs font-semibold text-blue-100">
              <span className="rounded-full border border-white/15 bg-white/10 px-4 py-2">
                AC & DC charging
              </span>
              <span className="rounded-full border border-white/15 bg-white/10 px-4 py-2">
                Multiple connectors
              </span>
              <span className="rounded-full border border-white/15 bg-white/10 px-4 py-2">
                Vehicle compatibility
              </span>
            </div>
          </div>

          <div className="rounded-[30px] border border-white/15 bg-white/10 p-6 shadow-2xl backdrop-blur-xl">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-100">
              Your charging overview
            </p>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/10 p-5">
                <Icon name="station" size={24} className="text-cyan-200" />
                <p className="mt-4 text-3xl font-black text-white">
                  {stations.length}
                </p>
                <p className="mt-1 text-xs font-medium text-blue-100">
                  Sample stations
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/10 p-5">
                <Icon name="battery" size={24} className="text-emerald-200" />
                <p className="mt-4 text-3xl font-black text-white">
                  {stations.reduce((sum, item) => sum + item.available, 0)}
                </p>
                <p className="mt-1 text-xs font-medium text-blue-100">
                  Sample available slots
                </p>
              </div>
            </div>

            <p className="mt-4 text-xs leading-6 text-blue-100/80">
              Demonstration data for the station discovery interface. Slot
              availability and prices are not live.
            </p>
          </div>
        </div>
      </section>

      {/* Filter section */}
      <section className="relative z-10 mx-auto -mt-7 max-w-7xl px-5 lg:px-8">
        <div className="overflow-visible rounded-[30px] border border-slate-200 bg-white p-5 shadow-xl shadow-slate-200/70 sm:p-7 lg:p-8">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                  <Icon name="sliders" size={19} />
                </span>
                <span className="text-xs font-extrabold uppercase tracking-[0.16em] text-blue-700">
                  Smart station discovery
                </span>
              </div>

              <h2 className="mt-3 text-2xl font-black tracking-tight text-[#10294b] sm:text-3xl">
                Refine your search
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                Choose your preferences to find a suitable charging station.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start rounded-full bg-blue-50 px-4 py-2 text-xs font-bold text-blue-700 sm:self-center">
              <Icon name="sliders" size={15} />
              {activeFilterCount} active filters
            </div>
          </div>

          {/* Search */}
          <div className="mt-7">
            <label className="mb-2 block text-xs font-bold uppercase tracking-[0.13em] text-slate-500">
              Search by station or location
            </label>

            <div className="flex min-h-[58px] items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 transition-all focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-50">
              <Icon name="search" size={21} className="text-blue-600" />
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search station name, area or location..."
                className="w-full bg-transparent text-sm font-medium text-slate-800 outline-none placeholder:text-slate-400"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  aria-label="Clear search"
                  className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
                >
                  <Icon name="close" size={17} />
                </button>
              )}
            </div>
          </div>

          {/* Custom filters */}
          <div className="relative mt-7 grid grid-cols-1 gap-x-5 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
            <AdvancedFilter
              label="Connector type"
              value={connector}
              options={connectorOptions}
              onChange={setConnector}
              icon="plug"
            />

            <AdvancedFilter
              label="Charger type"
              value={chargerType}
              options={chargerOptions}
              onChange={setChargerType}
              icon="station"
            />

            <AdvancedFilter
              label="Charging speed"
              value={speed}
              options={speedOptions}
              onChange={setSpeed}
              icon="gauge"
            />

            <AdvancedFilter
              label="Minimum power"
              value={minPower}
              options={powerOptions}
              onChange={setMinPower}
              icon="battery"
            />

            <AdvancedFilter
              label="Maximum price"
              value={maxPrice}
              options={priceOptions}
              onChange={setMaxPrice}
              icon="wallet"
            />

            <AdvancedFilter
              label="Availability status"
              value={status}
              options={statusOptions}
              onChange={setStatus}
              icon="activity"
            />
          </div>

          {/* Vehicle compatibility */}
          <div className="mt-8 rounded-[24px] border border-emerald-100 bg-gradient-to-r from-emerald-50/80 to-cyan-50/70 p-5 sm:p-6">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-emerald-700 shadow-sm">
                  <Icon name="car" size={23} />
                </span>
                <div>
                  <h3 className="font-extrabold text-slate-800">
                    Vehicle compatibility
                  </h3>
                  <p className="mt-1 max-w-lg text-xs leading-5 text-slate-500">
                    Select your vehicle connector to narrow down compatible
                    charging stations.
                  </p>
                </div>
              </div>

              <div className="w-full md:max-w-sm">
                <AdvancedFilter
                  label="Your vehicle connector"
                  value={vehicleConnector}
                  options={vehicleOptions}
                  onChange={setVehicleConnector}
                  icon="car"
                />
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
            <p className="text-xs text-slate-400">
              Filters update the station results automatically.
            </p>

            <button
              type="button"
              onClick={resetFilters}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-5 py-2.5 text-xs font-bold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              <Icon name="close" size={15} />
              Reset all filters
            </button>
          </div>
        </div>
      </section>

      {/* Station results */}
      <section className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <span className="text-xs font-extrabold uppercase tracking-[0.16em] text-blue-600">
              Discover charging destinations
            </span>
            <h2 className="mt-2 text-3xl font-black tracking-tight text-[#10294b]">
              Explore nearby options
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Charging station examples in Vijayawada.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowFavorites((previous) => !previous)}
            className={`inline-flex items-center justify-center gap-2 rounded-full border px-5 py-3 text-sm font-bold transition ${
              showFavorites
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-slate-200 bg-white text-slate-600 hover:border-rose-200 hover:text-rose-600"
            }`}
          >
            <Icon name="heart" size={17} />
            {showFavorites ? "Showing favourites" : "My favourites"}
            <span className="rounded-full bg-white px-2 py-0.5 text-xs">
              {favorites.length}
            </span>
          </button>
        </div>

        <div className="mt-7 flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
              <Icon name="station" size={19} />
            </span>
            <div>
              <p className="text-sm font-extrabold text-slate-800">
                {filteredStations.length} stations found
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Based on your selected preferences
              </p>
            </div>
          </div>

          <span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 sm:inline-flex">
            Demo station data
          </span>
        </div>

        {filteredStations.length > 0 ? (
          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {filteredStations.map((station) => (
              <StationCard
                key={station.id}
                station={station}
                favorite={favorites.includes(station.id)}
                onFavorite={() => toggleFavorite(station.id)}
                onDetails={() => setSelectedStation(station)}
              />
            ))}
          </div>
        ) : (
          <div className="mt-7 rounded-[28px] border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
            <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
              <Icon name="search" size={29} />
            </span>

            <h3 className="mt-5 text-xl font-extrabold text-slate-800">
              No matching stations found
            </h3>

            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
              Try changing your connector, power, price or availability
              preferences to see more charging stations.
            </p>

            <button
              type="button"
              onClick={resetFilters}
              className="mt-6 rounded-full bg-[#10294b] px-6 py-3 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              Clear all filters
            </button>
          </div>
        )}
      </section>

      {/* Station details modal */}
      {selectedStation && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#07182d]/70 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setSelectedStation(null);
            }
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="station-dialog-title"
            className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-[28px] bg-white p-6 shadow-2xl sm:p-8"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <span className="text-xs font-extrabold uppercase tracking-[0.15em] text-blue-600">
                  Station information
                </span>
                <h2
                  id="station-dialog-title"
                  className="mt-2 text-2xl font-black text-[#10294b]"
                >
                  {selectedStation.name}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setSelectedStation(null)}
                aria-label="Close station details"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600 transition hover:bg-slate-200"
              >
                <Icon name="close" size={19} />
              </button>
            </div>

            <div className="mt-6 rounded-2xl bg-gradient-to-br from-[#10294b] to-[#087c91] p-5 text-white">
              <div className="flex items-center gap-2 text-sm text-blue-100">
                <Icon name="pin" size={17} />
                {selectedStation.address}
              </div>

              <p className="mt-5 text-3xl font-black">
                {selectedStation.power} kW
              </p>
              <p className="mt-1 text-sm text-blue-100">
                {selectedStation.speed} charging power
              </p>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              {[
                ["Charger type", selectedStation.chargerType],
                ["Charging speed", selectedStation.speed],
                [
                  "Available slots",
                  `${selectedStation.available}/${selectedStation.total}`,
                ],
                ["Price", `₹${selectedStation.price}/kWh`],
                ["Connectors", selectedStation.connectors.join(", ")],
                ["Availability", selectedStation.status],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-2xl border border-slate-100 bg-slate-50 p-4"
                >
                  <p className="text-xs font-semibold text-slate-400">
                    {label}
                  </p>
                  <p className="mt-2 text-sm font-extrabold text-slate-800">
                    {value}
                  </p>
                </div>
              ))}
            </div>

            <p className="mt-5 text-sm leading-7 text-slate-500">
              {selectedStation.description}
            </p>

            <p className="mt-4 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">
              Demonstration information only. Station availability and prices
              are sample values, not live service data.
            </p>

            <button
              type="button"
              onClick={() => setSelectedStation(null)}
              className="mt-6 w-full rounded-xl bg-[#10294b] px-5 py-3.5 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              Close details
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-5 py-8 sm:flex-row lg:px-8">
          <BrandLogo compact />
          <p className="text-center text-xs text-slate-400">
            © 2026 ChargeMate AI. Smarter charging discovery.
          </p>
        </div>
      </footer>
    </main>
  );
}
