import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "glass" | "glow";
type ButtonSize = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    isLoading?: boolean;
    leftIcon?: ReactNode;
    rightIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className = "", variant = "primary", size = "md", isLoading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {

        const baseStyles = "inline-flex items-center justify-center rounded-xl font-bold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]";

        const variants = {
            primary: "bg-violet-600 text-white hover:bg-violet-500 shadow-[0_0_20px_rgba(124,58,237,0.3)] hover:shadow-[0_0_30px_rgba(124,58,237,0.5)] border border-violet-500/20",
            secondary: "bg-pink-600 text-white hover:bg-pink-500 shadow-[0_0_20px_rgba(244,63,94,0.3)] border border-pink-500/20",
            ghost: "text-white/60 hover:text-white hover:bg-white/5",
            danger: "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-colors",
            glass: "glass-button text-white hover:border-white/20 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]",
            glow: "bg-white text-black hover:scale-105 shadow-[0_0_20px_rgba(255,255,255,0.4)]",
        };

        const sizes = {
            sm: "px-3 py-1.5 text-xs gap-1.5",
            md: "px-5 py-2.5 text-sm gap-2",
            lg: "px-8 py-4 text-base gap-3",
            icon: "p-2 aspect-square",
        };

        return (
            <button
                ref={ref}
                disabled={isLoading || disabled}
                className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
                {...props}
            >
                {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <>
                        {leftIcon && <span className="shrink-0">{leftIcon}</span>}
                        {children}
                        {rightIcon && <span className="shrink-0">{rightIcon}</span>}
                    </>
                )}
            </button>
        );
    }
);

Button.displayName = "Button";
