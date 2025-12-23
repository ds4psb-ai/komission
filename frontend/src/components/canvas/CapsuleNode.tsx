import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Database, Lock, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

export type CapsuleStatus = "idle" | "running" | "done" | "error";

export type CapsuleParam = {
    key: string;
    label: string;
    type: "select" | "text" | "number" | "toggle";
    value?: string | number | boolean;
    options?: string[];
};

export type CapsuleDefinition = {
    id: string;
    title: string;
    summary: string;
    provider: string;
    inputs: string[];
    outputs: string[];
    params?: CapsuleParam[];
    status?: CapsuleStatus;
};

interface CapsuleNodeData {
    capsule?: CapsuleDefinition;
    status?: CapsuleStatus;
}

export const CapsuleNode = memo(({ data }: { data: CapsuleNodeData }) => {
    const capsule = (data.capsule ?? data) as CapsuleDefinition;
    const status = capsule.status ?? data.status ?? "idle";

    const statusStyles = {
        idle: "bg-white/20",
        running: "bg-amber-400 animate-pulse",
        done: "bg-emerald-400",
        error: "bg-red-500",
    } as const;

    return (
        <div
            className={cn(
                "glass-panel rounded-2xl min-w-[320px] overflow-hidden border border-rose-500/30 shadow-[0_0_30px_rgba(244,63,94,0.08)]"
            )}
        >
            <div className="px-5 py-3 border-b border-rose-500/20 bg-gradient-to-r from-rose-900/40 via-pink-900/20 to-transparent flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Lock className="w-4 h-4 text-rose-300" />
                    <span className="font-bold text-xs tracking-[0.3em] text-white/80 uppercase">
                        Capsule
                    </span>
                    <Badge variant="outline" intent="error" className="text-[9px] px-2 py-0.5 border-white/10 text-white/40">
                        SEALED
                    </Badge>
                </div>
                <div className="flex items-center gap-2">
                    <Badge
                        variant="glow"
                        intent={
                            status === 'running' ? 'warning' :
                                status === 'done' ? 'success' :
                                    status === 'error' ? 'error' : 'neutral'
                        }
                        className={cn("w-2 h-2 p-0 rounded-full", status === 'running' && "animate-pulse")}
                    />
                </div>
            </div>

            <div className="p-5 bg-black/60 backdrop-blur-xl space-y-4 relative">
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] pointer-events-none" />
                <div className="relative space-y-3">
                    <div>
                        <div className="text-[10px] text-white/40 uppercase tracking-wider">Capsule ID</div>
                        <div className="text-sm font-bold text-white">{capsule.title || "Capsule Node"}</div>
                        <p className="text-xs text-white/50 mt-1 leading-relaxed">
                            {capsule.summary || "외부 체인을 단일 노드로 캡슐화합니다."}
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-[11px] text-white/60">
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-3.5 h-3.5 text-rose-300" />
                            입력 {capsule.inputs?.length ?? 0}
                        </div>
                        <div className="flex items-center gap-2 justify-end">
                            출력 {capsule.outputs?.length ?? 0}
                        </div>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-white/50 border border-white/10 rounded-lg px-3 py-2 bg-white/5">
                        <Database className="w-3.5 h-3.5 text-rose-300" />
                        {capsule.provider || "Opal + NotebookLM"}
                    </div>

                    <div className="text-[10px] text-white/30 leading-relaxed">
                        내부 체인은 서버에서만 실행됩니다. 노출되는 것은 입력/출력 포트와 파라미터뿐입니다.
                    </div>
                </div>
            </div>

            <Handle type="target" position={Position.Left} className="!bg-rose-400 !w-3 !h-3 !border-2 !border-black" />
            <Handle type="source" position={Position.Right} className="!bg-rose-400 !w-3 !h-3 !border-2 !border-black" />
        </div>
    );
});

CapsuleNode.displayName = "CapsuleNode";
