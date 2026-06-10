import { cn } from "@/lib/utils";

const colors: Record<string, string> = {
  national: "bg-red-50 text-red-700",
  provincial: "bg-orange-50 text-orange-700",
  municipal: "bg-yellow-50 text-yellow-700",
  school: "bg-green-50 text-green-700",
  active: "bg-green-50 text-green-700",
  inactive: "bg-slate-100 text-slate-600",
  notice: "bg-blue-50 text-blue-700",
  policy: "bg-purple-50 text-purple-700",
};

export function Badge({ label, type }: { label: string; type?: string }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        type ? colors[type] || "bg-slate-100 text-slate-600" : "bg-slate-100 text-slate-600"
      )}
    >
      {label}
    </span>
  );
}
