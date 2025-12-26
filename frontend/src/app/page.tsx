"use client";

/**
 * Main Page - Unified Discover
 * 
 * Features:
 * - Compact search (link detection)
 * - Category tabs
 * - Campaign filter
 * - VirloVideoCard with embed modal
 * - Real outlier API with demo fallback
 */
import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, OutlierItem } from "@/lib/api";
import { AppHeader } from "@/components/AppHeader";
import { VirloVideoCard, VirloVideoItem } from "@/components/VirloVideoCard";
import {
  Search, Sparkles, TrendingUp, Link as LinkIcon, X,
  Users, Utensils, Smile, Palette, Dumbbell, ShoppingBag, Film
} from "lucide-react";

// Extended video type with campaign info
interface VideoWithCampaign extends VirloVideoItem {
  hasCampaign?: boolean;
  campaignType?: 'product' | 'visit' | 'delivery';
}

// Categories
const CATEGORIES = [
  { id: 'all', label: '전체', icon: Film },
  { id: 'meme', label: '밈', icon: Smile },
  { id: 'beauty', label: '뷰티', icon: Palette },
  { id: 'food', label: 'F&B', icon: Utensils },
  { id: 'fitness', label: '피트니스', icon: Dumbbell },
  { id: 'lifestyle', label: '라이프', icon: ShoppingBag },
];

// Campaign filter
const CAMPAIGN_FILTERS = [
  { id: 'all', label: '전체' },
  { id: 'with', label: '체험단 O' },
  { id: 'without', label: '체험단 X' },
];

// Demo data (fallback when API unavailable)
const DEMO_VIDEOS: VideoWithCampaign[] = [
  {
    id: 'demo-tiktok-1',
    video_url: 'https://www.tiktok.com/@khaby.lame/video/7019309323322220805',
    platform: 'tiktok',
    title: 'Khaby Lame - Life Hack Reactions 🙄',
    thumbnail_url: 'https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?w=400&h=600&fit=crop',
    creator: 'khaby.lame',
    category: 'meme',
    tags: ['viral', 'reaction'],
    view_count: 150000000,
    like_count: 12000000,
    engagement_rate: 0.08,
    outlier_tier: 'S',
    creator_avg_views: 50000000,
    analysis: { hook_pattern: 'visual_reaction', hook_score: 10, hook_duration_sec: 1.5 },
    hasCampaign: false,
    crawled_at: new Date().toISOString(),
  },
  {
    id: 'demo-beauty-1',
    video_url: 'https://www.tiktok.com/@skincare/video/123',
    platform: 'tiktok',
    title: '올리브영 신상 하울 🛒 가성비 꿀템!',
    thumbnail_url: 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=600&fit=crop',
    creator: 'beauty_lover',
    category: 'beauty',
    tags: ['올리브영', '하울'],
    view_count: 2800000,
    like_count: 180000,
    engagement_rate: 0.064,
    outlier_tier: 'A',
    creator_avg_views: 400000,
    analysis: { hook_pattern: 'unboxing', hook_score: 8, hook_duration_sec: 2.0 },
    hasCampaign: true,
    campaignType: 'product',
    crawled_at: new Date().toISOString(),
  },
  {
    id: 'demo-food-1',
    video_url: 'https://www.youtube.com/shorts/l_v3g7qx3vo',
    platform: 'youtube',
    title: '성수 핫플 카페 투어 ☕️',
    thumbnail_url: 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=600&fit=crop',
    creator: 'cafe_hunter',
    category: 'food',
    tags: ['성수', '카페'],
    view_count: 1500000,
    like_count: 95000,
    engagement_rate: 0.063,
    outlier_tier: 'A',
    creator_avg_views: 300000,
    analysis: { hook_pattern: 'aesthetic_reveal', hook_score: 8 },
    hasCampaign: true,
    campaignType: 'visit',
    crawled_at: new Date(Date.now() - 3600000).toISOString(),
  },
];

// Helper: Map OutlierItem to VideoWithCampaign
function mapOutlierToVideo(item: OutlierItem): VideoWithCampaign {
  return {
    id: item.id,
    video_url: item.video_url,
    platform: item.platform as 'tiktok' | 'instagram' | 'youtube',
    title: item.title || 'Untitled',
    thumbnail_url: item.thumbnail_url || undefined,
    category: item.category,
    view_count: item.view_count,
    like_count: item.like_count,
    engagement_rate: item.engagement_rate,
    outlier_tier: item.outlier_tier as 'S' | 'A' | 'B' | 'C' | null,
    outlier_score: item.outlier_score,
    creator_avg_views: item.creator_avg_views,
    crawled_at: item.crawled_at || undefined,
    hasCampaign: false,
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
  const [videos, setVideos] = useState<VideoWithCampaign[]>(DEMO_VIDEOS);
  const [isLoading, setIsLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [campaignFilter, setCampaignFilter] = useState('all');

  const isLinkMode = isVideoUrl(searchInput);

  // Fetch real outliers from API
  useEffect(() => {
    async function fetchOutliers() {
      try {
        const response = await api.listOutliers({ limit: 50 });
        if (response.items && response.items.length > 0) {
          const mapped = response.items.map(mapOutlierToVideo);
          setVideos(mapped);
        }
      } catch {
        console.log('Using demo data (API unavailable)');
      } finally {
        setIsLoading(false);
      }
    }
    fetchOutliers();
  }, []);

  // Filter videos
  const filteredVideos = videos.filter(v => {
    if (selectedCategory !== 'all' && v.category !== selectedCategory) return false;
    if (campaignFilter === 'with' && !v.hasCampaign) return false;
    if (campaignFilter === 'without' && v.hasCampaign) return false;

    if (searchInput && !isLinkMode) {
      const q = searchInput.toLowerCase();
      return v.title.toLowerCase().includes(q) ||
        v.creator?.toLowerCase().includes(q) ||
        v.tags?.some(t => t.toLowerCase().includes(q));
    }
    return true;
  });

  const campaignCount = videos.filter(v => v.hasCampaign).length;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!searchInput.trim() || !isLinkMode) return;

    setIsSubmitting(true);

    try {
      const url = searchInput.trim();
      const platform = detectPlatform(url);
      const node = await api.createRemixNode({ title: 'New Analysis', source_video_url: url, platform });
      try { await api.analyzeNode(node.node_id); } catch { }
      router.push(`/remix/${node.node_id}`);
    } catch (error: unknown) {
      console.error(error);
      const err = error as { message?: string };
      if (err.message?.includes('401')) router.push('/login');
      else alert('분석 실패');
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans">
      <AppHeader />

      {/* Header + Search */}
      <section className="px-6 pt-6 pb-3 max-w-7xl mx-auto">
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
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1 px-2 py-1 bg-white/5 rounded-lg text-white/60"><TrendingUp className="w-3 h-3 text-emerald-400" />{videos.length}</div>
            <div className="flex items-center gap-1 px-2 py-1 bg-violet-500/10 rounded-lg text-violet-300"><Users className="w-3 h-3" />체험단 {campaignCount}</div>
          </div>
        </div>
      </section>

      {/* Filter Bar */}
      <section className="px-6 py-2 max-w-7xl mx-auto border-b border-white/5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Categories */}
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${selectedCategory === cat.id ? 'bg-white text-black' : 'bg-white/5 text-white/60 hover:text-white hover:bg-white/10'
                  }`}
              >
                <cat.icon className="w-3 h-3" />{cat.label}
              </button>
            ))}
          </div>

          {/* Campaign Filter */}
          <div className="flex items-center gap-1">
            {CAMPAIGN_FILTERS.map(f => (
              <button
                key={f.id}
                onClick={() => setCampaignFilter(f.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${campaignFilter === f.id
                    ? f.id === 'with' ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30' : 'bg-white/10 text-white border border-white/20'
                    : 'text-white/40 hover:text-white/70'
                  }`}
              >
                {f.id === 'with' && <Users className="w-3 h-3 inline mr-1" />}{f.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Video Grid */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm text-white/50">
            {selectedCategory !== 'all' && <span className="text-white mr-1">{CATEGORIES.find(c => c.id === selectedCategory)?.label}</span>}
            {campaignFilter === 'with' && <span className="text-violet-300">체험단 </span>}
            <span>{filteredVideos.length}개</span>
          </h2>
          {isLoading && <span className="text-xs text-white/40">로딩중...</span>}
        </div>

        {filteredVideos.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-3xl mb-3">🔍</div>
            <div className="text-white/50 text-sm">결과가 없습니다</div>
            <button onClick={() => { setSelectedCategory('all'); setCampaignFilter('all'); setSearchInput(''); }} className="mt-3 text-xs text-violet-400">필터 초기화</button>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredVideos.map(video => (
              <div key={video.id} className="relative">
                <VirloVideoCard
                  video={video}
                  variant="compact"
                  showAnalysis={true}
                  onPlay={() => router.push(`/video/${video.id}`)}
                />
                {video.hasCampaign && (
                  <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-violet-500 text-[9px] font-bold text-white rounded-md flex items-center gap-0.5 z-20">
                    <Users className="w-2.5 h-2.5" />체험단
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
