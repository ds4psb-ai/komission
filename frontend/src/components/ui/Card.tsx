import { HTMLAttributes, forwardRef } from "react";

type CardVariant = "default" | "hover" | "outline" | "neon";
type CardPadding = "none" | "sm" | "md" | "lg";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: CardVariant;
    padding?: CardPadding;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className = "", variant = "default", padding = "md", children, ...props }, ref) => {

        const baseStyles = "rounded-2xl transition-all duration-300";

        const variants = {
            default: "glass-panel",
            hover: "glass-panel glass-panel-hover cursor-pointer",
            outline: "border border-white/10 bg-transparent",
            neon: "p-[1px] bg-gradient-to-r from-[rgb(var(--color-violet))] via-[rgb(var(--color-pink))] to-[rgb(var(--color-orange))]",
        };

        const paddings = {
            none: "",
            sm: "p-4",
            md: "p-6",
            lg: "p-8",
        };

        // Special handling for neon variant wrapper
        if (variant === "neon") {
            return (
                <div ref={ref} className={`${baseStyles} ${variants.neon} ${className}`} {...props}>
                    <div className={`bg-[var(--background)] h-full w-full rounded-[15px] ${paddings[padding]}`}>
                        {children}
                    </div>
                </div>
            );
        }

        return (
            <div
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${paddings[padding]} ${className}`}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = "Card";
