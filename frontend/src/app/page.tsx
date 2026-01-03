"use client";

/**
 * Main Page - Unified Outlier Discovery
 * 
 * Features:
 * - Platform filter (TikTok/YouTube/Instagram)
 * - Category tabs
 * - Tier filter
 * - UnifiedOutlierCard with 9:16 vertical layout
 * - Real outlier API with demo fallback
 */
import { useState, useEffect, useRef, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, OutlierItem } from "@/lib/api";
import { useAuthGate, AUTH_ACTIONS } from "@/lib/useAuthGate";
import { UnifiedOutlierCard, OutlierCardItem } from "@/components/UnifiedOutlierCard";
import { SessionHUD } from "@/components/SessionHUD";
import {
  Search, Sparkles, TrendingUp, Link as LinkIcon, X,
  Smile, Palette, Utensils, Dumbbell, ShoppingBag, Film,
  Award, Star, Diamond, BarChart, RefreshCw, Loader2, Brush
} from "lucide-react";
import { useTranslations, useLocale } from 'next-intl';
import { LanguageToggle } from '@/components/ui/LanguageToggle';

// Category IDs (labels from translations)
const CATEGORY_IDS = ['all', 'meme', 'beauty', 'food', 'fitness', 'lifestyle', 'art'] as const;
const CATEGORY_ICONS: Record<string, typeof Film> = {
  all: Film, meme: Smile, beauty: Palette, food: Utensils, fitness: Dumbbell, lifestyle: ShoppingBag, art: Brush
};

// Tier IDs (labels from translations)
const TIER_IDS = ['all', 'S', 'A', 'B', 'C'] as const;
const TIER_ICONS: Record<string, typeof Award | null> = {
  all: null, S: Award, A: Star, B: Diamond, C: BarChart
};

// Empty fallback - no more hardcoded demo data
const DEMO_ITEMS: OutlierCardItem[] = [];

// Helper: Map OutlierItem to OutlierCardItem
function mapToCardItem(item: OutlierItem): OutlierCardItem {
  return {
    id: item.id,
    external_id: item.external_id,
    video_url: item.video_url,
    platform: item.platform as 'tiktok' | 'instagram' | 'youtube',
    title: item.title || 'Untitled',
    thumbnail_url: item.thumbnail_url || undefined,
    category: item.category,
    view_count: item.view_count,
    like_count: item.like_count,
    share_count: item.share_count,
    outlier_score: item.outlier_score,
    outlier_tier: item.outlier_tier as 'S' | 'A' | 'B' | 'C' | null,
    creator_avg_views: item.creator_avg_views,
    engagement_rate: item.engagement_rate,
    crawled_at: item.crawled_at || undefined,
    status: item.status as 'pending' | 'selected' | 'rejected' | 'promoted',
    // VDG Analysis - pass through for VDG badge display
    vdg_analysis: item.vdg_analysis,
  };
}

// URL detection
function isVideoUrl(input: string): boolean {
  return input.includes('tiktok.com') || input.includes('instagram.com') || input.includes('youtube.com');
}

function detectPlatform(url: string): 'tiktok' | 'instagram' | 'youtube' {
  if (url.includes('tiktok')) return 'tiktok';
  if (url.includes('instagram')) return 'instagram';
  return 'youtube';
}

export default function Home() {
  const router = useRouter();
  const [items, setItems] = useState<OutlierCardItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isMountedRef = useRef(true);
  const t = useTranslations('pages.home');
  const tCommon = useTranslations('common');
  const tCategories = useTranslations('categories');
  const tTiers = useTranslations('tiers');
  const tPlatforms = useTranslations('platforms');
  const locale = useLocale();

  // Filters
  const [platform, setPlatform] = useState('all');
  const [category, setCategory] = useState('all');
  const [tier, setTier] = useState('all');

  const isLinkMode = isVideoUrl(searchInput);

  // Fetch outliers
  useEffect(() => {
    fetchOutliers();
  }, [platform, tier]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  async function fetchOutliers() {
    if (isMountedRef.current) {
      setIsLoading(true);
    }
    try {
      const params: Record<string, string> = {
        limit: '50',
        status: 'promoted',
        analysis_status: 'completed'  // Only show fully analyzed videos on main page
      };
      if (platform !== 'all') params.platform = platform;
      if (tier !== 'all') params.tier = tier;

      const response = await api.listOutliers(params);
      if (!isMountedRef.current) return;
      if (response.items && response.items.length > 0) {
        setItems(response.items.map(mapToCardItem));
      } else {
        setItems(DEMO_ITEMS);
      }
    } catch {
      console.log('Using demo data');
      if (!isMountedRef.current) return;
      setItems(DEMO_ITEMS);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }

  // Filter items
  const filteredItems = items.filter(item => {
    if (category !== 'all' && item.category !== category) return false;
    if (searchInput && !isLinkMode) {
      const q = searchInput.toLowerCase();
      return item.title.toLowerCase().includes(q);
    }
    return true;
  });

  // Stats
  const tierCounts = {
    S: items.filter(i => i.outlier_tier === 'S').length,
    A: items.filter(i => i.outlier_tier === 'A').length,
  };

  // Auth gate for protected actions
  const { requireAuth } = useAuthGate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!searchInput.trim() || !isLinkMode) return;

    // Require auth for video analysis
    if (!requireAuth(AUTH_ACTIONS.ANALYZE)) return;

    setIsSubmitting(true);
    try {
      const url = searchInput.trim();
      const plat = detectPlatform(url);
      const node = await api.createRemixNode({ title: 'New Analysis', source_video_url: url, platform: plat });
      try { await api.analyzeNode(node.node_id); } catch { }
      router.push(`/remix/${node.node_id}`);
    } catch (error: unknown) {
      const err = error as { message?: string };
      if (err.message?.includes('401')) router.push('/login');
      else alert('Analysis failed');
      setIsSubmitting(false);
    }
  }

  async function handlePromote(item: OutlierCardItem) {
    // Require auth for promote action
    if (!requireAuth(AUTH_ACTIONS.PROMOTE)) return;

    try {
      await fetch(`/api/v1/outliers/items/${item.id}/promote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      router.push(`/canvas`);
    } catch {
      alert('Promotion failed');
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans pb-20 md:pb-0 pt-6">

      <main id="feed-content" className="relative z-10 px-4 sm:px-6 max-w-[1920px] mx-auto min-h-screen pb-20">

        {/* Floating Filter Bar */}
        <section className="sticky top-4 z-40 mb-8 animate-slideUp">
          <div className="glass-panel rounded-2xl p-2 flex flex-col xl:flex-row items-center justify-between gap-4 border border-white/10 shadow-2xl bg-black/60 backdrop-blur-xl">

            {/* 1. Platform & Category */}
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar w-full xl:w-auto px-2">
              <div className="flex bg-white/5 rounded-xl p-1 shrink-0">
                <button
                  onClick={() => setPlatform('all')}
                  className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'all' ? 'bg-white text-black shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                >{tPlatforms('all')}</button>
                <button
                  onClick={() => setPlatform('tiktok')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'tiktok' ? 'bg-black text-white shadow-lg border border-white/20' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                >
                  <div className="w-3.5 h-3.5">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
                    </svg>
                  </div>
                  <span className="hidden sm:inline">{tPlatforms('tiktok')}</span>
                </button>
                <button
                  onClick={() => setPlatform('youtube')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'youtube' ? 'bg-[#FF0000] text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                >
                  <div className="w-3.5 h-3.5">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                    </svg>
                  </div>
                  <span className="hidden sm:inline">{tPlatforms('shorts')}</span>
                </button>
                <button
                  onClick={() => setPlatform('instagram')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'instagram' ? 'bg-gradient-to-r from-[#f09433] via-[#e6683c] to-[#dc2743] text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                >
                  <div className="w-3.5 h-3.5">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                    </svg>
                  </div>
                  <span className="hidden sm:inline">{tPlatforms('reels')}</span>
                </button>
              </div>

              <div className="w-[1px] h-8 bg-white/10 mx-2 shrink-0" />

              {CATEGORY_IDS.map(catId => {
                const Icon = CATEGORY_ICONS[catId];
                return (
                  <button
                    key={catId}
                    onClick={() => setCategory(catId)}
                    className={`hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all shrink-0 ${category === catId
                      ? 'bg-[#c1ff00] text-black shadow-[0_0_15px_rgba(193,255,0,0.3)]'
                      : 'text-white/50 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    <Icon className="w-3 h-3" />{tCategories(catId)}
                  </button>
                );
              })}
            </div>


            {/* 3. Tier Filter */}
            <div className="hidden lg:flex items-center bg-white/5 rounded-xl p-1 gap-1">
              {TIER_IDS.map(tierId => (
                <button
                  key={tierId}
                  onClick={() => setTier(tierId)}
                  className={`px-3 py-2 rounded-lg text-[10px] font-bold transition-all ${tier === tierId
                    ? 'bg-white text-black'
                    : 'text-white/40 hover:text-white'
                    }`}
                >
                  {tTiers(tierId.toLowerCase())}
                </button>
              ))}
            </div>


            {/* Language Toggle */}
            <LanguageToggle currentLocale={locale} />
          </div>
        </section>

        {/* Masonry Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-40">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-[#c1ff00]/20 border-t-[#c1ff00] rounded-full animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[#c1ff00] animate-pulse">AI</div>
            </div>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-40 text-white/30">
            <div className="text-4xl mb-4">🕸️</div>
            <p>{t('emptyState')}</p>
          </div>
        ) : (
          <div className="masonry-grid stagger-reveal">
            {filteredItems.map((item, idx) => (
              <div key={item.id} className="masonry-item" style={{ animationDelay: `${idx * 0.05}s` }}>
                <UnifiedOutlierCard item={item} />
              </div>
            ))}
          </div>
        )}
      </main>

      {/* <SessionHUD /> */}
    </div >
  );
}
