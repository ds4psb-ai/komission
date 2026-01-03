"use client";

/**
 * Session Input Page - 상황 입력 (Polished)
 * 
 * - Motion animations for entry and selection
 * - Enhanced visuals for categories/platforms
 */
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from '@/contexts/SessionContext';
import { motion, stagger } from 'framer-motion';
import { Sparkles, ChevronRight, Package, Tag, Smartphone } from 'lucide-react';
import { useTranslations } from 'next-intl';

const CATEGORIES = [
    { value: 'beauty', label: '뷰티', icon: '💄', color: 'from-pink-500 to-rose-500' },
    { value: 'food', label: '푸드', icon: '🍜', color: 'from-orange-500 to-amber-500' },
    { value: 'fashion', label: '패션', icon: '👗', color: 'from-[#c1ff00] to-emerald-500' },
    { value: 'tech', label: '테크', icon: '📱', color: 'from-cyan-500 to-blue-500' },
    { value: 'lifestyle', label: '라이프', icon: '🏠', color: 'from-emerald-500 to-green-500' },
    { value: 'entertainment', label: '엔터', icon: '🎬', color: 'from-fuchsia-500 to-pink-500' },
];

const PLATFORMS = [
    { value: 'tiktok', label: 'TikTok', icon: '🎵', color: 'bg-black' },
    { value: 'youtube', label: 'Shorts', icon: '▶️', color: 'bg-red-600' },
    { value: 'instagram', label: 'Reels', icon: '📷', color: 'bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-500' },
];

export default function SessionInputPage() {
    const router = useRouter();
    const { setInputContext } = useSession();

    const [product, setProduct] = useState('');
    const [category, setCategory] = useState('');
    const [platform, setPlatform] = useState<'tiktok' | 'youtube' | 'instagram'>('tiktok');

    const isValid = category && platform;

    const handleSubmit = () => {
        if (!isValid) return;

        setInputContext({
            product: product || undefined,
            category,
            platform,
        });

        router.push('/session/result');
    };

    // Animation variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                delayChildren: stagger(0.1, { from: "first" })
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <div className="min-h-screen bg-transparent pb-24">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-[#050505]/80 border-b border-white/5">
                <div className="flex items-center gap-2 max-w-lg mx-auto">
                    <Sparkles className="w-5 h-5 text-violet-400" />
                    <h1 className="text-lg font-bold">내 상황 입력</h1>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-4 py-8">
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-10"
                >
                    {/* Product Input */}
                    <motion.section variants={itemVariants} className="space-y-4">
                        <label className="flex items-center gap-2 text-sm font-bold text-white/80">
                            <Package className="w-4 h-4 text-violet-400" />
                            어떤 제품인가요? <span className="text-white/30 font-normal">(선택)</span>
                        </label>
                        <input
                            type="text"
                            value={product}
                            onChange={(e) => setProduct(e.target.value)}
                            placeholder="예: 립틴트, 에어프라이어, 후드티"
                            className="w-full px-5 py-4 rounded-2xl bg-white/5 border border-white/10 text-white placeholder:text-white/20 focus:border-violet-500/50 focus:bg-white/10 focus:outline-none transition-all"
                        />
                    </motion.section>

                    {/* Category Selection */}
                    <motion.section variants={itemVariants} className="space-y-4">
                        <label className="flex items-center gap-2 text-sm font-bold text-white/80">
                            <Tag className="w-4 h-4 text-violet-400" />
                            카테고리 <span className="text-amber-500">*</span>
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                            {CATEGORIES.map((cat) => {
                                const isSelected = category === cat.value;
                                return (
                                    <motion.button
                                        key={cat.value}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => setCategory(cat.value)}
                                        className={`
                                            relative flex flex-col items-center gap-2 px-3 py-4 rounded-2xl border transition-all duration-300
                                            ${isSelected
                                                ? 'bg-white/10 border-white/30 ring-1 ring-white/30 shadow-lg'
                                                : 'bg-white/5 border-white/5 hover:bg-white/10'
                                            }
                                        `}
                                    >
                                        <div className={`
                                            text-2xl p-2 rounded-xl transition-all duration-300
                                            ${isSelected ? `bg-gradient-to-br ${cat.color} opacity-100` : 'bg-white/5 opacity-80'}
                                        `}>
                                            {cat.icon}
                                        </div>
                                        <span className={`text-xs font-medium ${isSelected ? 'text-white' : 'text-white/50'}`}>
                                            {cat.label}
                                        </span>
                                        {isSelected && (
                                            <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-violet-400 shadow-[0_0_10px_rgba(167,139,250,0.5)]" />
                                        )}
                                    </motion.button>
                                );
                            })}
                        </div>
                    </motion.section>

                    {/* Platform Selection */}
                    <motion.section variants={itemVariants} className="space-y-4">
                        <label className="flex items-center gap-2 text-sm font-bold text-white/80">
                            <Smartphone className="w-4 h-4 text-violet-400" />
                            플랫폼 <span className="text-amber-500">*</span>
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                            {PLATFORMS.map((plat) => {
                                const isSelected = platform === plat.value;
                                return (
                                    <motion.button
                                        key={plat.value}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => setPlatform(plat.value as typeof platform)}
                                        className={`
                                            flex flex-col items-center gap-2 px-3 py-4 rounded-2xl border transition-all duration-300
                                            ${isSelected
                                                ? 'bg-white/10 border-white/30 ring-1 ring-white/30'
                                                : 'bg-white/5 border-white/5 hover:bg-white/10'
                                            }
                                        `}
                                    >
                                        <div className={`
                                            w-10 h-10 rounded-full flex items-center justify-center text-lg
                                            ${plat.color} ${isSelected ? 'scale-110 shadow-lg' : 'opacity-80 grayscale'}
                                            transition-all duration-300
                                        `}>
                                            {plat.icon}
                                        </div>
                                        <span className={`text-xs font-medium ${isSelected ? 'text-white' : 'text-white/50'}`}>
                                            {plat.label}
                                        </span>
                                    </motion.button>
                                );
                            })}
                        </div>
                    </motion.section>

                    {/* Submit Button */}
                    <motion.div variants={itemVariants} className="pt-6">
                        <motion.button
                            onClick={handleSubmit}
                            disabled={!isValid}
                            whileHover={isValid ? { scale: 1.02 } : {}}
                            whileTap={isValid ? { scale: 0.98 } : {}}
                            className={`
                                w-full flex items-center justify-center gap-2 py-5 rounded-2xl font-bold text-lg transition-all duration-300
                                ${isValid
                                    ? 'bg-[#c1ff00] text-black shadow-[0_0_20px_rgba(193,255,0,0.4)]'
                                    : 'bg-white/5 text-white/20 cursor-not-allowed border border-white/5'
                                }
                            `}
                        >
                            <span>패턴 추천받기</span>
                            <ChevronRight className={`w-5 h-5 ${isValid ? 'stroke-[3]' : ''}`} />
                        </motion.button>
                    </motion.div>
                </motion.div>
            </main>
        </div>
    );
}
