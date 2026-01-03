"use client";
import { useTranslations } from 'next-intl';

import { useEffect, useMemo, useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Boxes, Sparkles } from "lucide-react";
import { api, Pipeline } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

type TemplateCard = {
    id: string;
    title: string;
    summary: string;
    category: string;
    author: string;
    nodeCount?: number;
    updatedAt?: string;
    templateId?: string;
    isLive: boolean;
};

const curatedTemplates: TemplateCard[] = [
    {
        id: "auteur-hook-reveal",
        title: "Hook → Reveal 3-Beat",
        summary: "3초 훅 + 6초 증명 + 4초 CTA의 안정적인 구조.",
        category: "Beauty",
        author: "Komission Lab",
        nodeCount: 6,
        isLive: false,
    },
    {
        id: "auteur-meme-snapcut",
        title: "Meme Snapcut",
        summary: "밈 텍스트 + 컷 5개로 리듬을 극대화.",
        category: "Meme",
        author: "Komission Lab",
        nodeCount: 7,
        isLive: false,
    },
    {
        id: "auteur-vlog-arc",
        title: "Vlog Arc 20s",
        summary: "일상 시작-전환-결론이 분명한 브릿지 구조.",
        category: "Lifestyle",
        author: "Komission Lab",
        nodeCount: 5,
        isLive: false,
    },
    {
        id: "auteur-product-promise",
        title: "Product Promise",
        summary: "효능 전-후 비교 + 핵심 근거 2개.",
        category: "Commerce",
        author: "Komission Lab",
        nodeCount: 8,
        isLive: false,
    },
    {
        id: "auteur-contrast-loop",
        title: "Contrast Loop",
        summary: "Before/After 반복으로 리텐션을 끌어올림.",
        category: "Beauty",
        author: "Komission Lab",
        nodeCount: 6,
        isLive: false,
    },
    {
        id: "auteur-quick-proof",
        title: "Quick Proof Stack",
        summary: "증거 컷 3개 + CTA를 빠르게 고정.",
        category: "Meme",
        author: "Komission Lab",
        nodeCount: 4,
        isLive: false,
    },
];

export function TemplateGallery() {
    const router = useRouter();
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        const loadTemplates = async () => {
            try {
                const list = await api.listPublicPipelines();
                if (!isMountedRef.current) return;
                setPipelines(list.slice(0, 6));
            } catch (err) {
                console.warn("템플릿 로드 실패:", err);
            } finally {
                if (isMountedRef.current) {
                    setLoading(false);
                }
            }
        };

        loadTemplates();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const templates = useMemo<TemplateCard[]>(() => {
        if (pipelines.length) {
            const live = pipelines.map((p) => ({
                id: p.id,
                title: p.title,
                summary: "커뮤니티에서 검증된 워크플로우 템플릿.",
                category: "Community",
                author: "Verified Creator",
                nodeCount: (p.graph_data?.nodes || []).length,
                updatedAt: p.updated_at,
                templateId: p.id,
                isLive: true,
            }));
            if (live.length >= 6) return live.slice(0, 6);
            return [...live, ...curatedTemplates.slice(0, 6 - live.length)];
        }
        return curatedTemplates;
    }, [pipelines]);

    const handleUseTemplate = (template: TemplateCard) => {
        if (template.templateId) {
            router.push(`/canvas?templateId=${template.templateId}`);
            return;
        }
        router.push("/pipelines");
    };

    return (
        <section className="mt-16">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between mb-8">
                <div>
                    <div className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-white/40">
                        <span className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                        Template Studio
                    </div>
                    <h3 className="text-2xl md:text-3xl font-black text-white mt-2">
                        실전형 캡슐 템플릿
                    </h3>
                    <p className="text-sm text-white/50 mt-2 max-w-xl">
                        검증된 워크플로우를 바로 캔버스로 불러오고, 필요한 파라미터만 커스터마이징하세요.
                    </p>
                </div>
                <div className="flex gap-3">
                    <Link
                        href="/pipelines"
                        className="text-xs font-bold text-white/60 hover:text-white transition-colors inline-flex items-center gap-1"
                    >
                        전체 템플릿 보기 <ArrowRight className="w-3 h-3" />
                    </Link>
                    <Button
                        variant="glass"
                        size="sm"
                        rightIcon={<Sparkles className="w-3 h-3" />}
                        onClick={() => router.push("/canvas")}
                    >
                        새 템플릿 시작
                    </Button>
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div
                            key={`template-skeleton-${i}`}
                            className="h-[220px] rounded-2xl border border-white/10 bg-white/5 animate-pulse"
                        />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {templates.map((template, index) => (
                        <motion.div
                            key={template.id}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.4, delay: index * 0.05 }}
                        >
                            <Card
                                variant="outline"
                                className={cn(
                                    "relative h-full border-white/10 bg-black/60 hover:border-pink-500/40 hover:shadow-[0_0_30px_rgba(236,72,153,0.15)]"
                                )}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <div className="text-[10px] uppercase tracking-[0.25em] text-white/40">
                                            {template.category}
                                        </div>
                                        <h4 className="text-lg font-bold text-white mt-2">
                                            {template.title}
                                        </h4>
                                    </div>
                                    <div
                                        className={cn(
                                            "text-[10px] px-2 py-1 rounded-full border",
                                            template.isLive
                                                ? "border-emerald-500/30 text-emerald-300"
                                                : "border-white/10 text-white/30"
                                        )}
                                    >
                                        {template.isLive ? "LIVE" : "LAB"}
                                    </div>
                                </div>

                                <p className="text-sm text-white/50 leading-relaxed min-h-[48px]">
                                    {template.summary}
                                </p>

                                <div className="mt-5 grid grid-cols-2 gap-3 text-[11px] text-white/50">
                                    <div className="flex items-center gap-2">
                                        <Boxes className="w-3.5 h-3.5 text-pink-400" />
                                        {template.nodeCount ?? 0} 노드
                                    </div>
                                    <div className="text-right">
                                        {template.updatedAt
                                            ? new Date(template.updatedAt).toLocaleDateString()
                                            : "검증 중"}
                                    </div>
                                </div>

                                <div className="mt-6 flex items-center justify-between">
                                    <div className="text-[11px] text-white/40">
                                        {template.author}
                                    </div>
                                    <Button
                                        size="sm"
                                        variant={template.isLive ? "primary" : "ghost"}
                                        onClick={() => handleUseTemplate(template)}
                                        rightIcon={<ArrowRight className="w-3 h-3" />}
                                    >
                                        {template.isLive ? "템플릿 사용" : "미리보기"}
                                    </Button>
                                </div>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            )}
        </section>
    );
}
