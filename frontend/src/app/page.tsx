"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, RemixNode } from "@/lib/api";
import { AppHeader } from "@/components/AppHeader";
import { OutlierCard } from "@/components/OutlierCard";
import { TemplateGallery } from "@/components/TemplateGallery";

export default function Home() {
  const router = useRouter();
  const [nodes, setNodes] = useState<RemixNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [urlInput, setUrlInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>("");

  useEffect(() => {
    fetchNodes();
  }, []);

  async function fetchNodes() {
    try {
      const data = await api.listRemixNodes({ limit: 50 });
      setNodes(data);
    } catch (err) {
      console.warn("아웃라이어 로드 실패:", err);
      // Fallback mock data for development/demo
      setNodes([
        {
          id: "demo-1",
          node_id: "demo-1",
          title: "불닭볶음면 챌린지 🔥",
          platform: "tiktok",
          layer: "master",
          view_count: 1250000,
          performance_delta: "+127%",
          created_at: new Date().toISOString(),
        },
        {
          id: "demo-2",
          node_id: "demo-2",
          title: "성수 팝업 브이로그",
          platform: "instagram",
          layer: "fork",
          view_count: 890000,
          performance_delta: "+89%",
          created_at: new Date().toISOString(),
        },
        {
          id: "demo-3",
          node_id: "demo-3",
          title: "올리브영 하울 🛒",
          platform: "youtube",
          layer: "fork_of_fork",
          view_count: 456000,
          performance_delta: "+45%",
          created_at: new Date().toISOString(),
        },
      ] as any);
    } finally {
      setLoading(false);
    }
  }

  async function handleUrlSubmit(e: FormEvent) {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsSubmitting(true);
    setLoadingStage("🔍 URL 분석 중...");

    try {
      const url = urlInput.trim();
      const platform = url.includes('tiktok') ? 'tiktok'
        : url.includes('instagram') ? 'instagram'
          : 'youtube';

      await new Promise(r => setTimeout(r, 800));
      setLoadingStage("🧠 콘텐츠 생성 중...");

      const node = await api.createRemixNode({
        title: 'New Magic Project',
        source_video_url: url,
        platform
      });

      await new Promise(r => setTimeout(r, 800));
      setLoadingStage("🚀 최종 결과 최적화...");

      try {
        await api.analyzeNode(node.node_id);
      } catch (e) {
        console.warn("Analysis trigger warning:", e);
      }

      router.push(`/remix/${node.node_id}`);

    } catch (error: any) {
      console.error(error);
      // Check if it's an authentication error
      if (error.message?.includes('credentials') || error.message?.includes('401') || error.message?.includes('인증')) {
        if (confirm('로그인이 필요합니다. 로그인 페이지로 이동할까요?')) {
          router.push('/login');
        }
      } else {
        alert('분석에 실패했습니다. 올바른 URL인지 확인해주세요.');
      }
      setIsSubmitting(false);
      setLoadingStage("");
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-32 font-sans selection:bg-violet-500/30 selection:text-white">
      <AppHeader />

      {/* Hero Section - Compact Magic Input */}
      <section className="relative px-6 pt-12 pb-16 max-w-[1920px] mx-auto border-b border-white/5">
        {/* Ambient Background Spotlights */}
        <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-[-10%] right-[10%] w-[400px] h-[400px] bg-pink-600/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative z-10 flex flex-col xl:flex-row xl:items-end justify-between gap-10">

          {/* Header / Title */}
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-white/60 mb-6 hover:bg-white/10 transition-colors cursor-default">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              실시간 바이럴 인텔리전스 v2.0
            </div>

            <h2 className="text-5xl md:text-6xl font-black tracking-tight text-white mb-4 leading-[1.1]">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400">Komission</span>
              <span className="block text-3xl md:text-4xl text-white/40 mt-2 font-medium">바이럴의 법칙을 발견하세요.</span>
            </h2>
          </div>

          {/* Magic Input Bar - Enhanced */}
          <div className="w-full xl:w-auto flex-shrink-0">
            <form onSubmit={handleUrlSubmit} className="relative group w-full xl:w-[600px]">
              {/* Glow Effect */}
              <div className={`absolute -inset-0.5 bg-gradient-to-r from-violet-600 via-pink-600 to-orange-600 rounded-2xl opacity-50 group-hover:opacity-100 blur transition duration-1000 ${isSubmitting ? 'animate-pulse' : ''}`} />

              <div className="relative flex items-center bg-[#0a0a0a] border border-white/10 rounded-2xl p-2 shadow-2xl">
                <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center text-xl text-white/20">
                  🔗
                </div>
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="인스타그램, 틱톡 링크를 붙여넣으세요..."
                  className="w-full bg-transparent text-lg text-white placeholder-white/30 focus:outline-none h-12 px-2 font-medium"
                  disabled={isSubmitting}
                />
                <button
                  type="submit"
                  disabled={isSubmitting || !urlInput.trim()}
                  className={`
                    h-12 px-6 rounded-xl font-bold text-sm transition-all duration-300 flex items-center gap-2 flex-shrink-0
                    ${isSubmitting
                      ? 'bg-white/10 text-white/40 cursor-wait'
                      : 'bg-white text-black hover:bg-violet-50 hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(255,255,255,0.2)]'
                    }
                  `}
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span>분석중</span>
                    </>
                  ) : (
                    <>
                      <span>✨ 매직 생성</span>
                      <span className="text-lg">→</span>
                    </>
                  )}
                </button>
              </div>

              {/* Loading Status */}
              <div className={`absolute -bottom-8 left-2 text-sm font-bold transition-all duration-300 ${isSubmitting ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}`}>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400 animate-pulse">
                  {loadingStage}
                </span>
              </div>
            </form>

            {/* Quick Links */}
            {!isSubmitting && (
              <div className="mt-4 flex gap-3 text-xs font-medium text-white/30 px-2 overflow-x-auto no-scrollbar">
                <span>🔥 인기 태그:</span>
                <span className="hover:text-white cursor-pointer transition-colors">#불닭볶음면</span>
                <span className="hover:text-white cursor-pointer transition-colors">#성수팝업</span>
                <span className="hover:text-white cursor-pointer transition-colors">#올리브영추천</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Grid Section */}
      <main className="container mx-auto px-6 py-12 max-w-[1920px]">

        {/* Section Title */}
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="w-2 h-8 bg-violet-500 rounded-full mr-2"></span>
            최근 발견된 아웃라이어
          </h3>

          <div className="flex gap-2">
            <button className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors text-white/60">
              ⚡️
            </button>
            <button className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors text-white/60">
              📅
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-40">
            <div className="relative w-20 h-20">
              <div className="absolute inset-0 rounded-full border-4 border-violet-500/20"></div>
              <div className="absolute inset-0 rounded-full border-4 border-violet-500 border-t-transparent animate-spin"></div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            {nodes.map((node, index) => (
              <OutlierCard key={node.id} node={node as any} index={index} />
            ))}

            {/* Empty State Card */}
            <div className="group block relative aspect-[9/16] rounded-3xl border-2 border-dashed border-white/10 bg-white/5 hover:bg-white/10 transition-colors cursor-pointer flex flex-col items-center justify-center text-center p-6"
              onClick={() => document.querySelector('input')?.focus()}>
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <span className="text-3xl text-white/30">+</span>
              </div>
              <p className="text-sm font-bold text-white/50">새로운 분석 시작하기</p>
              <p className="text-xs text-white/30 mt-1">상단 URL을 입력하세요</p>
            </div>
          </div>
        )}

        <TemplateGallery />
      </main>
    </div>
  );
}
