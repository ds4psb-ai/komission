"use client";

import Link from "next/link";

export default function TermsPage() {
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
                        ← 홈으로 돌아가기
                    </Link>
                    <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400 mb-4">
                        이용약관
                    </h1>
                    <p className="text-white/40 text-sm">
                        최종 수정일: 2024년 12월 23일
                    </p>
                </div>

                {/* Content */}
                <div className="space-y-10 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제1조 (목적)
                        </h2>
                        <p>
                            본 약관은 Komission(이하 &quot;회사&quot;)이 제공하는 바이럴 콘텐츠 인텔리전스 플랫폼 서비스(이하 &quot;서비스&quot;)의
                            이용조건 및 절차, 회사와 이용자의 권리·의무 및 책임사항 등을 규정함을 목적으로 합니다.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제2조 (서비스의 내용)
                        </h2>
                        <p className="mb-4">회사가 제공하는 서비스는 다음과 같습니다:</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>바이럴 콘텐츠 분석 및 패턴 발굴 서비스</li>
                            <li>AI 기반 콘텐츠 리믹스 및 최적화 추천</li>
                            <li>콘텐츠 계보(Genealogy) 추적 및 시각화</li>
                            <li>크리에이터 로열티 및 리워드 시스템</li>
                            <li>O2O(Online to Offline) 캠페인 연동 서비스</li>
                            <li>실시간 트렌드 분석 및 인사이트 제공</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제3조 (이용자의 의무)
                        </h2>
                        <p className="mb-4">이용자는 다음 행위를 하여서는 안 됩니다:</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>타인의 정보를 도용하거나 허위 정보를 등록하는 행위</li>
                            <li>서비스를 이용하여 얻은 정보를 회사의 사전 승낙 없이 상업적으로 이용하는 행위</li>
                            <li>회사 또는 제3자의 지적재산권을 침해하는 행위</li>
                            <li>서비스의 정상적인 운영을 방해하는 행위</li>
                            <li>자동화된 수단(봇, 스크래퍼 등)을 이용한 무단 접근 행위</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제4조 (콘텐츠 및 지적재산권)
                        </h2>
                        <p className="mb-4">
                            이용자가 서비스에 업로드하거나 분석 요청하는 콘텐츠에 대한 저작권은 원저작자에게 귀속됩니다.
                            이용자는 본인이 적법한 권리를 보유하거나 이용 허락을 받은 콘텐츠만을 서비스에 등록할 수 있습니다.
                        </p>
                        <p>
                            회사는 서비스 개선 및 AI 학습 목적으로 익명화된 분석 데이터를 활용할 수 있으며,
                            이 과정에서 이용자의 개인정보는 처리되지 않습니다.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제5조 (포인트 및 로열티)
                        </h2>
                        <p className="mb-4">
                            회사는 이용자의 활동에 따라 K-Point(이하 &quot;포인트&quot;)를 지급할 수 있습니다.
                            포인트는 다음과 같은 기준으로 적립됩니다:
                        </p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>원본 콘텐츠가 Fork(리믹스)될 때 원작자에게 로열티 지급</li>
                            <li>콘텐츠 조회수 마일스톤 달성 시 보너스 포인트</li>
                            <li>O2O 캠페인 참여 및 미션 완료 시 리워드</li>
                            <li>연속 출석 및 일일 미션 완료 보상</li>
                        </ul>
                        <p className="mt-4 text-white/50 text-sm">
                            ※ 포인트의 현금 전환, 유효기간 및 사용 조건은 별도 공지에 따릅니다.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제6조 (면책조항)
                        </h2>
                        <p>
                            회사는 천재지변, 시스템 장애, 제3자의 악의적 행위 등 불가항력적인 사유로 인해
                            서비스를 제공할 수 없는 경우 책임을 지지 않습니다. 또한, AI 분석 결과는 참고 자료로서 제공되며,
                            이를 기반으로 한 이용자의 의사결정에 대해 회사는 책임을 지지 않습니다.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-violet-500 rounded-full" />
                            제7조 (분쟁 해결)
                        </h2>
                        <p>
                            본 약관과 관련하여 발생하는 분쟁은 대한민국 법률을 준거법으로 하며,
                            서울중앙지방법원을 제1심 관할법원으로 합니다.
                        </p>
                    </section>

                    {/* Footer */}
                    <div className="pt-10 border-t border-white/10">
                        <div className="flex flex-wrap gap-4 text-sm">
                            <Link href="/privacy" className="text-white/40 hover:text-white transition-colors">
                                개인정보처리방침 →
                            </Link>
                            <Link href="/login" className="text-white/40 hover:text-white transition-colors">
                                로그인 페이지 →
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
