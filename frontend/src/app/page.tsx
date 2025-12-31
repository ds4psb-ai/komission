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
  Award, Star, Diamond, BarChart, RefreshCw, Loader2
} from "lucide-react";

// Platform filter
// Platform/Category filters
// Note: Platform filter UI is hardcoded in the render method to use SVGs

// Categories
const CATEGORIES = [
  { id: 'all', label: '전체', icon: Film },
  { id: 'meme', label: '밈', icon: Smile },
  { id: 'beauty', label: '뷰티', icon: Palette },
  { id: 'food', label: 'F&B', icon: Utensils },
  { id: 'fitness', label: '피트니스', icon: Dumbbell },
  { id: 'lifestyle', label: '라이프', icon: ShoppingBag },
];

// Tier filter
const TIERS = [
  { id: 'all', label: '모든 티어', icon: null },
  { id: 'S', label: 'S-Tier', icon: Award },
  { id: 'A', label: 'A-Tier', icon: Star },
  { id: 'B', label: 'B-Tier', icon: Diamond },
  { id: 'C', label: 'C-Tier', icon: BarChart },
];

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
      const params: Record<string, string> = { limit: '50', status: 'promoted' };
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
      else alert('분석 실패');
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
      alert('승격 실패');
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans pb-20 md:pb-0">

      {/* Header + Search */}
      <section className="px-4 sm:px-6 pt-6 pb-3 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          {/* Search */}
          <form onSubmit={handleSubmit} className="flex-1 max-w-lg">
            <div className="flex items-center bg-white/5 border border-white/10 rounded-xl px-3 py-2 focus-within:border-violet-500/50 transition-colors">
              {isLinkMode ? <LinkIcon className="w-4 h-4 text-violet-400 mr-2" /> : <Search className="w-4 h-4 text-white/40 mr-2" />}
              <input
                type="text"
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                placeholder="검색 또는 링크 붙여넣기..."
                className="flex-1 bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
                disabled={isSubmitting}
              />
              {searchInput && <button type="button" onClick={() => setSearchInput('')} className="p-1 text-white/40 hover:text-white"><X className="w-3 h-3" /></button>}
              {isLinkMode && (
                <button type="submit" disabled={isSubmitting} className="ml-2 px-3 py-1 bg-violet-500 hover:bg-violet-400 rounded-lg text-xs font-bold text-white flex items-center gap-1">
                  {isSubmitting ? <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-3 h-3" />}
                  분석
                </button>
              )}
            </div>
          </form>

          {/* Stats */}
          <div className="flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1 px-2 py-1 bg-white/5 rounded-lg text-white/60">
              <TrendingUp className="w-3 h-3 text-emerald-400" />{items.length}
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 rounded-lg text-amber-300">
              <Award className="w-3 h-3" />S: {tierCounts.S}
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-purple-500/10 rounded-lg text-purple-300">
              <Star className="w-3 h-3" />A: {tierCounts.A}
            </div>
            <button
              onClick={fetchOutliers}
              disabled={isLoading}
              className="p-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-white/50 hover:text-white transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </section>

      {/* Filter Bar */}
      <section className="px-4 sm:px-6 py-3 max-w-7xl mx-auto border-b border-white/5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          {/* Platform Filter */}
          <div className="flex bg-white/5 border border-white/10 rounded-xl p-1 gap-1">
            <button
              onClick={() => setPlatform('all')}
              className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'all' ? 'bg-white text-black shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
            >
              전체
            </button>
            <button
              onClick={() => setPlatform('tiktok')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'tiktok' ? 'bg-black text-white shadow-lg border border-white/20' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
            >
              <div className="w-3.5 h-3.5">
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                  <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
                </svg>
              </div>
              <span className="hidden sm:inline">TikTok</span>
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
              <span className="hidden sm:inline">Shorts</span>
            </button>
            <button
              onClick={() => setPlatform('instagram')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platform === 'instagram' ? 'bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
            >
              <div className="w-3.5 h-3.5">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
                  <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                  <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                </svg>
              </div>
              <span className="hidden sm:inline">Reels</span>
            </button>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${category === cat.id
                  ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                  : 'text-white/50 hover:text-white hover:bg-white/5'
                  }`}
              >
                <cat.icon className="w-3 h-3" />{cat.label}
              </button>
            ))}
          </div>

          {/* Tier Filter */}
          <div className="flex items-center gap-1 ml-auto">
            {TIERS.map(t => (
              <button
                key={t.id}
                onClick={() => setTier(t.id)}
                className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${tier === t.id
                  ? t.id === 'S' ? 'bg-amber-500/20 text-amber-300'
                    : t.id === 'A' ? 'bg-purple-500/20 text-purple-300'
                      : 'bg-white/10 text-white'
                  : 'text-white/40 hover:text-white/70'
                  }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Video Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm text-white/50">
            {platform !== 'all' && <span className="text-white mr-1">{platform === 'tiktok' ? 'TikTok' : platform === 'youtube' ? 'Shorts' : platform === 'instagram' ? 'Reels' : ''}</span>}
            {category !== 'all' && <span className="text-violet-300 mr-1">{CATEGORIES.find(c => c.id === category)?.label}</span>}
            {tier !== 'all' && <span className="text-amber-300 mr-1">{tier}-Tier</span>}
            <span>{filteredItems.length}개</span>
          </h2>
        </div>

        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-3xl mb-3">🔍</div>
            <div className="text-white/50 text-sm">결과가 없습니다</div>
            <button
              onClick={() => { setPlatform('all'); setCategory('all'); setTier('all'); setSearchInput(''); }}
              className="mt-3 text-xs text-violet-400"
            >
              필터 초기화
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredItems.map(item => (
              <UnifiedOutlierCard
                key={item.id}
                item={item}
              />
            ))}
          </div>
        )}
      </main>

      <SessionHUD />
    </div>
  );
}
