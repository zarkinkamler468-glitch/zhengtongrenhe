import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-xl border border-white/80 bg-white/90 px-3 py-2 text-sm shadow-sm outline-none transition",
        "focus:border-blue-300 focus:ring-2 focus:ring-blue-100",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
