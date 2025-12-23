import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

const badgeVariants = cva(
    "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold font-mono tracking-tight transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default:
                    "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
                secondary:
                    "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
                destructive:
                    "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
                outline: "text-foreground border border-[var(--glass-border)]",
                soft: "bg-white/5 text-white/70 border border-white/5 backdrop-blur-sm",
                glow: "bg-black/40 border backdrop-blur-md shadow-lg",
            },
            intent: {
                brand: "border-violet-500/20 text-violet-300 bg-violet-500/10 shadow-[0_0_10px_rgba(124,58,237,0.1)]",
                success: "border-emerald-500/20 text-emerald-300 bg-emerald-500/10 shadow-[0_0_10px_rgba(52,211,153,0.1)]",
                warning: "border-orange-500/20 text-orange-300 bg-orange-500/10 shadow-[0_0_10px_rgba(251,146,60,0.1)]",
                error: "border-pink-500/20 text-pink-300 bg-pink-500/10 shadow-[0_0_10px_rgba(244,63,94,0.1)]",
                cyan: "border-cyan-500/20 text-cyan-300 bg-cyan-500/10 shadow-[0_0_10px_rgba(34,211,238,0.1)]",
                neutral: "border-white/10 text-white/40 bg-white/5",
            }
        },
        compoundVariants: [
            {
                variant: "glow",
                intent: "brand",
                class: "border-violet-500/30 shadow-[0_0_15px_rgba(124,58,237,0.2)]"
            },
            {
                variant: "glow",
                intent: "success",
                class: "border-emerald-500/30 shadow-[0_0_15px_rgba(52,211,153,0.2)]"
            },
            {
                variant: "glow",
                intent: "error",
                class: "border-pink-500/30 shadow-[0_0_15px_rgba(244,63,94,0.2)]"
            },
            {
                variant: "glow",
                intent: "cyan",
                class: "border-cyan-500/30 shadow-[0_0_15px_rgba(34,211,238,0.2)]"
            }
        ],
        defaultVariants: {
            variant: "soft",
            intent: "neutral",
        },
    }
);

export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> { }

function Badge({ className, variant, intent, ...props }: BadgeProps) {
    return (
        <div className={cn(badgeVariants({ variant, intent }), className)} {...props} />
    );
}

export { Badge, badgeVariants };
