import { HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type CardVariant = "default" | "hover" | "outline" | "neon";
type CardPadding = "none" | "sm" | "md" | "lg";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: CardVariant;
    padding?: CardPadding;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className = "", variant = "default", padding = "md", children, ...props }, ref) => {

        const baseStyles = "rounded-2xl transition-all duration-500 border relative overflow-hidden";

        const variants = {
            default: "glass-panel bg-black/40 border-white/10",
            hover: "glass-panel glass-panel-hover cursor-pointer bg-black/40 hover:bg-white/5",
            outline: "border border-white/10 bg-transparent hover:border-white/20",
            neon: "glass-panel border-violet-500/30 text-glow box-shadow-[0_0_20px_rgba(124,58,237,0.1)]",
        };

        const paddings = {
            none: "",
            sm: "p-4",
            md: "p-6",
            lg: "p-8",
        };

        // Special handling for neon variant wrapper (Gradient Border)
        if (variant === "neon") {
            return (
                <div ref={ref} className="group relative rounded-2xl p-[1px] bg-gradient-to-r from-violet-600/50 via-pink-600/50 to-cyan-600/50 hover:via-pink-500 hover:to-cyan-500 transition-all duration-500" {...props}>
                    <div className={`relative h-full w-full bg-black/90 rounded-[15px] ${paddings[padding]} backdrop-blur-xl`}>
                        {children}
                    </div>
                </div>
            );
        }

        return (
            <div
                ref={ref}
                className={cn(baseStyles, variants[variant], paddings[padding], className)}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = "Card";
