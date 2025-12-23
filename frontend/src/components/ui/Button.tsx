import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "glass";
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

        const baseStyles = "inline-flex items-center justify-center rounded-xl font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]";

        const variants = {
            primary: "bg-[rgb(var(--color-violet))] text-white hover:bg-[rgb(var(--color-violet))/0.9] shadow-[0_0_20px_rgba(var(--color-violet),0.4)] hover:shadow-[0_0_30px_rgba(var(--color-violet),0.6)]",
            secondary: "bg-[rgb(var(--color-pink))] text-white hover:bg-[rgb(var(--color-pink))/0.9] shadow-[0_0_20px_rgba(var(--color-pink),0.4)]",
            ghost: "text-white/70 hover:text-white hover:bg-white/5",
            danger: "bg-[rgb(var(--color-danger))] text-white hover:bg-[rgb(var(--color-danger))/0.9]",
            glass: "glass-button text-white",
        };

        const sizes = {
            sm: "px-3 py-1.5 text-xs gap-1.5",
            md: "px-5 py-2.5 text-sm gap-2",
            lg: "px-8 py-4 text-base gap-3",
            icon: "p-2",
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
