import { InputHTMLAttributes, forwardRef, ReactNode } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    leftIcon?: ReactNode;
    rightIcon?: ReactNode;
    error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className = "", leftIcon, rightIcon, error, ...props }, ref) => {

        return (
            <div className={`relative flex items-center group hero-input-wrapper ${className}`}>
                {/* Left Icon */}
                {leftIcon && (
                    <div className="absolute left-4 text-white/40 group-focus-within:text-[rgb(var(--color-violet))] transition-colors pointer-events-none">
                        {leftIcon}
                    </div>
                )}

                <input
                    ref={ref}
                    className={`
            w-full bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 
            focus:outline-none focus:border-[rgb(var(--color-violet))] focus:ring-1 focus:ring-[rgb(var(--color-violet))] 
            transition-all duration-300
            disabled:opacity-50 disabled:cursor-not-allowed
            ${leftIcon ? "pl-11" : "pl-4"}
            ${rightIcon ? "pr-11" : "pr-4"}
            ${props.size === 1 ? "py-2 text-sm" : "py-3"}
            ${error ? "border-[rgb(var(--color-danger))] focus:border-[rgb(var(--color-danger))] focus:ring-[rgb(var(--color-danger))]" : ""}
          `}
                    {...props}
                />

                {/* Right Icon */}
                {rightIcon && (
                    <div className="absolute right-4 text-white/40 pointer-events-none">
                        {rightIcon}
                    </div>
                )}
            </div>
        );
    }
);

Input.displayName = "Input";
