import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const variants = {
      primary:
        "bg-blue-600 text-white hover:bg-blue-500 shadow-md shadow-blue-600/20",
      secondary:
        "bg-white/90 text-slate-700 border border-white/80 hover:bg-white shadow-sm",
      ghost: "text-slate-600 hover:bg-blue-50 hover:text-blue-600",
      danger: "bg-red-600 text-white hover:bg-red-500 shadow-sm",
    };
    const sizes = {
      sm: "px-3 py-1.5 text-sm rounded-xl",
      md: "px-4 py-2 text-sm rounded-xl",
      lg: "px-6 py-3 text-base rounded-xl",
    };
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
