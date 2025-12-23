import { HTMLAttributes, forwardRef } from "react";

type BadgeVariant = "solid" | "subtle" | "outline";
type BadgeColor = "violet" | "pink" | "cyan" | "orange" | "emerald" | "default";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    variant?: BadgeVariant;
    color?: BadgeColor;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
    ({ className = "", variant = "subtle", color = "default", children, ...props }, ref) => {

        const baseStyles = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ring-1 ring-inset uppercase tracking-wide";

        const colorMap = {
            violet: "rgb(var(--color-violet))",
            pink: "rgb(var(--color-pink))",
            cyan: "rgb(var(--color-cyan))",
            orange: "rgb(var(--color-orange))",
            emerald: "rgb(var(--color-emerald))",
            default: "255 255 255",
        };

        const c = colorMap[color];

        const variants = {
            solid: `bg-[rgb(${c})] text-white ring-transparent shadow-[0_0_10px_rgba(${c},0.4)]`,
            subtle: `bg-[rgba(${c},0.1)] text-[rgb(${c})] ring-[rgba(${c},0.2)]`,
            outline: `bg-transparent text-[rgb(${c})] ring-[rgba(${c},0.4)]`,
        };

        return (
            <span
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${className}`}
                {...props}
            >
                {children}
            </span>
        );
    }
);

Badge.displayName = "Badge";
