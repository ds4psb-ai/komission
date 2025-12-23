// frontend/src/components/remix/VariableSlotEditor.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import type { VariableSlot } from "@/lib/types/session";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface VariableSlotEditorProps {
    slots?: VariableSlot[];
    onChange?: (slotId: string, value: unknown) => void;
}

export function VariableSlotEditor({ slots, onChange }: VariableSlotEditorProps) {
    const storeSlots = useSessionStore((s) => s.slots);
    const patchSlot = useSessionStore((s) => s.patchSlot);

    const activeSlots = slots || storeSlots;

    if (!activeSlots || activeSlots.length === 0) {
        return null;
    }

    const handleChange = (slotId: string, value: unknown) => {
        patchSlot(slotId, value);
        onChange?.(slotId, value);
    };

    return (
        <Card className="space-y-4">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold flex items-center gap-2">
                    🎯 커스터마이즈
                </h2>
                <Badge variant="subtle" color="pink">
                    편집 가능한 슬롯
                </Badge>
            </div>

            <div className="space-y-4">
                {activeSlots.map((slot) => (
                    <div key={slot.slotId} className="space-y-2">
                        <label className="flex items-center justify-between">
                            <span className="text-sm font-bold text-white/80">
                                {slot.label}
                                {slot.required && <span className="text-[rgb(var(--color-pink))] ml-1">*</span>}
                            </span>
                            {slot.kind === "toggle" && (
                                <button
                                    onClick={() => handleChange(slot.slotId, !slot.value)}
                                    className={`w-12 h-6 rounded-full transition-all ${slot.value
                                            ? "bg-[rgb(var(--color-violet))]"
                                            : "bg-white/20"
                                        }`}
                                >
                                    <div
                                        className={`w-5 h-5 rounded-full bg-white shadow-lg transform transition-transform ${slot.value ? "translate-x-6" : "translate-x-0.5"
                                            }`}
                                    />
                                </button>
                            )}
                        </label>

                        {slot.kind === "text" && (
                            <Input
                                type="text"
                                value={(slot.value as string) || ""}
                                onChange={(e) => handleChange(slot.slotId, e.target.value)}
                                placeholder={`${slot.label} 입력...`}
                            />
                        )}

                        {slot.kind === "number" && (
                            <Input
                                type="number"
                                value={(slot.value as number) || 0}
                                onChange={(e) => handleChange(slot.slotId, parseFloat(e.target.value))}
                            />
                        )}

                        {slot.kind === "choice" && Array.isArray(slot.value) && (
                            <div className="flex flex-wrap gap-2">
                                {(slot.value as string[]).map((option, idx) => (
                                    <Button
                                        key={idx}
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleChange(slot.slotId, option)}
                                        className="border border-white/10 hover:border-[rgb(var(--color-violet))]"
                                    >
                                        {option}
                                    </Button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </Card>
    );
}
