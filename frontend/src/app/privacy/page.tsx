"use client";

import Link from "next/link";
import { useTranslations } from 'next-intl';

export default function PrivacyPage() {
    const t = useTranslations('legal.privacy');
    const tLegal = useTranslations('legal');

    return (
        <div className="min-h-screen bg-[#050505] text-white py-20 px-6 selection:bg-violet-500/30">
            {/* Background Aurora */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-20%] right-[-10%] w-[50vw] h-[50vw] bg-pink-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] left-[-10%] w-[50vw] h-[50vw] bg-violet-600/10 rounded-full blur-[120px]" />
            </div>

            <div className="relative z-10 max-w-3xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <Link href="/" className="inline-flex items-center gap-2 text-white/40 hover:text-white text-sm font-medium transition-colors mb-8">
                        ← {tLegal('backHome')}
                    </Link>
                    <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-violet-400 mb-4">
                        {t('title')}
                    </h1>
                    <p className="text-white/40 text-sm">
                        {t('lastUpdated')}
                    </p>
                </div>

                {/* Content */}
                <div className="space-y-10 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.1.title')}
                        </h2>
                        <p className="mb-4">
                            {t('sections.1.content')}
                        </p>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            <h3 className="font-bold text-white mb-3">{t('sections.1.reqTitle')}</h3>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                                {(t.raw('sections.1.reqItems') as string[]).map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                            <h3 className="font-bold text-white mb-3 mt-6">{t('sections.1.optTitle')}</h3>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                                {(t.raw('sections.1.optItems') as string[]).map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.2.title')}
                        </h2>
                        <p className="mb-4">{t('sections.2.content')}</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.2.items') as string[]).map((item, i) => (
                                <li key={i} dangerouslySetInnerHTML={{ __html: item }} />
                            ))}
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.3.title')}
                        </h2>
                        <p className="mb-4">
                            {t('sections.3.content')}
                        </p>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10 space-y-3 text-sm">
                            {(t.raw('sections.3.items') as { label: string, value: string }[]).map((item, i) => (
                                <div key={i} className="flex justify-between">
                                    <span>{item.label}</span>
                                    <span className="text-white font-bold">{item.value}</span>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.4.title')}
                        </h2>
                        <p className="mb-4">
                            {t('sections.4.content')}
                        </p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.4.items') as string[]).map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.5.title')}
                        </h2>
                        <p className="mb-4">{t('sections.5.content')}</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.5.items') as string[]).map((item, i) => (
                                <li key={i} dangerouslySetInnerHTML={{ __html: item }} />
                            ))}
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.6.title')}
                        </h2>
                        <p className="mb-4">{t('sections.6.content')}</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            {(t.raw('sections.6.items') as string[]).map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                        <p className="mt-4 text-white/50 text-sm">
                            {t('sections.6.note')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.7.title')}
                        </h2>
                        <p>
                            {t('sections.7.content')}
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.8.title')}
                        </h2>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            <p className="mb-4">
                                {t('sections.8.content')}
                            </p>
                            <div className="space-y-2 text-sm">
                                {(t.raw('sections.8.items') as string[]).map((item, i) => (
                                    <p key={i} dangerouslySetInnerHTML={{ __html: item }} />
                                ))}
                            </div>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            {t('sections.9.title')}
                        </h2>
                        <p>
                            {t('sections.9.content')}
                        </p>
                    </section>

                    {/* Footer */}
                    <div className="pt-10 border-t border-white/10">
                        <div className="flex flex-wrap gap-4 text-sm">
                            <Link href="/terms" className="text-white/40 hover:text-white transition-colors">
                                {tLegal('gotoTerms')} →
                            </Link>
                            <Link href="/login" className="text-white/40 hover:text-white transition-colors">
                                {tLegal('loginPage')} →
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
