import { memo, useState } from "react";
import { useRouter } from "next/navigation";
import { Handle, Position } from "@xyflow/react";
import { Database, Lock, Sparkles, Wand2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { GuideNodeData } from "./CustomNodes";
import { NodeWrapper } from "./NodeWrapper";
import { HANDLE_STYLES } from "./utils";

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
    // Phase 3: Creator Persona (implicit signals)
    persona_context?: {
        style_vector?: Record<string, number>;
        calibration_summary?: string;
        signal_source?: 'behavior' | 'calibration' | 'hybrid';
    };
};

interface CapsuleNodeData {
    capsule?: CapsuleDefinition;
    status?: CapsuleStatus;
    onComplete?: (guideData: GuideNodeData) => void;
}

export const CapsuleNode = memo(({ data }: { data: CapsuleNodeData }) => {
    const router = useRouter();
    const capsule = (data.capsule ?? data) as CapsuleDefinition;
    const [localStatus, setLocalStatus] = useState<CapsuleStatus>(capsule.status ?? data.status ?? "idle");

    const handleRun = () => {
        setLocalStatus('running');
        // Simulate Server Process (Opal + NotebookLM)
        setTimeout(() => {
            setLocalStatus('done');
            if (data.onComplete) {
                data.onComplete({
                    hook: "Wait, you've been cutting onions wrong this whole time? 🧅",
                    shotlist: [
                        "Close up of tearing up while cutting onion",
                        "Show 'wet paper towel' hack",
                        "Demonstrate perfect dicing with no tears",
                        "Final dish reveal (Onion Soup)"
                    ],
                    audio: "Trending: 'Lofi Chef' by BeatMaster",
                    scene: "Kitchen, Natural Light, 45 degree angle",
                    timing: ["1.5", "3.0", "4.0", "2.0"],
                    do_not: ["Don't use dull knife", "Don't look at camera directly"]
                });
            }
        }, 2500);
    };

    return (
        <NodeWrapper
            title="Capsule"
            colorClass="border-rose-500/30"
            status={localStatus}
            icon={<Lock className="w-4 h-4 text-rose-300" />}
            viralBadge="SEALED"
            className="min-w-[320px]"
        >

            <div className="space-y-4">
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

                    {localStatus === 'idle' && (
                        <button
                            onClick={handleRun}
                            disabled={localStatus !== 'idle'}
                            className="w-full py-2.5 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(244,63,94,0.15)] group focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Wand2 className="w-3.5 h-3.5 group-hover:rotate-12 transition-transform" />
                            Generate Guide (Auto)
                        </button>
                    )}

                    {localStatus === 'running' && (
                        <div className="text-xs text-amber-400 text-center animate-pulse font-bold">
                            Capsule Processing...
                        </div>
                    )}

                    {localStatus === 'done' && (
                        <div className="space-y-2">
                            <div className="text-xs text-emerald-400 text-center font-bold flex items-center justify-center gap-1">
                                <span>✓ Guide Generated</span>
                            </div>
                            <button
                                onClick={() => router.push('/o2o/campaigns/create')}
                                className="w-full py-2 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 text-orange-300 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(249,115,22,0.15)]"
                            >
                                📍 O2O 캠페인 열기
                            </button>
                        </div>
                    )}

                    <div className="text-[10px] text-white/30 leading-relaxed mt-2 pt-2 border-t border-white/5">
                        내부 체인은 서버에서만 실행됩니다. 노출되는 것은 입력/출력 포트와 파라미터뿐입니다.
                    </div>
                </div>
            </div>

            <Handle type="target" position={Position.Left} className={HANDLE_STYLES.rose} />
            <Handle type="source" position={Position.Right} className={HANDLE_STYLES.rose} />

        </NodeWrapper >
    );
});

CapsuleNode.displayName = "CapsuleNode";
