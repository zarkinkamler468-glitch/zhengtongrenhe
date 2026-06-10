"use client";

type MapMarkerProps = {
  variant: "hub" | "province";
  size?: "hero" | "section";
  name?: string;
  showLabel?: boolean;
  floatIndex?: number;
};

export function MapMarker({
  variant,
  size = "hero",
  name,
  showLabel = false,
  floatIndex = 0,
}: MapMarkerProps) {
  const isHub = variant === "hub";
  const isHero = size === "hero";

  const orbSize = isHub ? (isHero ? "h-3 w-3" : "h-3.5 w-3.5") : isHero ? "h-2 w-2" : "h-2.5 w-2.5";
  const floatDelay = `${(floatIndex % 9) * 0.45}s`;

  const orbClass = isHub
    ? "bg-amber-400 shadow-[0_2px_8px_rgba(251,191,36,0.45)]"
    : "bg-emerald-500 shadow-[0_2px_6px_rgba(16,185,129,0.4)]";

  return (
    <>
      <span
        className="map-marker-float pointer-events-none absolute bottom-1/2 left-1/2 flex flex-col items-center"
        style={{ animationDelay: floatDelay }}
      >
        <span className={`block rounded-full ring-2 ring-white/90 ${orbSize} ${orbClass}`} />
        <span
          className={`mt-0.5 w-px bg-gradient-to-b ${
            isHub ? "from-amber-400/70" : "from-emerald-500/60"
          } to-transparent ${isHub ? "h-3" : "h-2.5"}`}
          aria-hidden
        />
      </span>

      {showLabel && name && (
        <span className="pointer-events-none absolute left-1/2 top-full mt-1.5 -translate-x-1/2 whitespace-nowrap rounded-md bg-white/90 px-2 py-0.5 text-[10px] font-medium text-slate-600 shadow-sm ring-1 ring-slate-200/60">
          {name}
        </span>
      )}
    </>
  );
}
