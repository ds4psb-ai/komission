"use client";

import Link from "next/link";
import { useTranslations } from 'next-intl';

export default function TermsPage() {
    const t = useTranslations('legal.terms');
    const tLegal = useTranslations('legal');

    return (
        <div className="min-h-screen bg-[#050505] text-white py-20 px-6 selection:bg-violet-500/30">
            {/* Background Aurora */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] bg-violet-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50vw] h-[50vw] bg-pink-600/10 rounded-full blur-[120px]" />
            </div>

            <div className="relative z-10 max-w-3xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <Link href="/" className="inline-flex items-center gap-2 text-white/40 hover:text-white text-sm font-medium transition-colors mb-8">
                        ← {tLegal('backHome')}
                    </Link>
                    <h1 className="text-4xl font-black text-white italic uppercase tracking-tighter mb-4">
                        <span className="text-[#c1ff00] drop-shadow-[0_0_15px_rgba(193,255,0,0.5)]">TERMS</span> & CONDITIONS
                    </h1>
                    <p className="text-white/40 text-sm">
                        {t('lastUpdated')}
                    </p>
                </div>

                {/* Content */}
                <div className="space-y-10 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.1.title')}
                        </h2>
                        <p>
                            {t('sections.1.content')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.2.title')}
                        </h2>
                        <p className="mb-4">{t('sections.2.content')}</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.2.items') as string[]).map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.3.title')}
                        </h2>
                        <p className="mb-4">{t('sections.3.content')}</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.3.items') as string[]).map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.4.title')}
                        </h2>
                        <p className="mb-4">
                            {t('sections.4.content1')}
                        </p>
                        <p>
                            {t('sections.4.content2')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.5.title')}
                        </h2>
                        <p className="mb-4">
                            {t('sections.5.content')}
                        </p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.5.items') as string[]).map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                        <p className="mt-4 text-white/50 text-sm">
                            {t('sections.5.note')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.6.title')}
                        </h2>
                        <p>
                            {t('sections.6.content')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            {t('sections.7.title')}
                        </h2>
                        <p>
                            {t('sections.7.content')}
                        </p>
                    </section>

                    {/* Footer */}
                    <div className="pt-10 border-t border-white/10">
                        <div className="flex flex-wrap gap-4 text-sm">
                            <Link href="/privacy" className="text-white/40 hover:text-white transition-colors">
                                {tLegal('gotoPrivacy')} →
                            </Link>
                            <Link href="/login" className="text-white/40 hover:text-white transition-colors">
                                {tLegal('loginPage')} →
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
}
