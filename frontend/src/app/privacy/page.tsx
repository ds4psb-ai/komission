"use client";

import Link from "next/link";

export default function PrivacyPage() {
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
                        ← 홈으로 돌아가기
                    </Link>
                    <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-violet-400 mb-4">
                        개인정보처리방침
                    </h1>
                    <p className="text-white/40 text-sm">
                        최종 수정일: 2024년 12월 23일
                    </p>
                </div>

                {/* Content */}
                <div className="space-y-10 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제1조 (개인정보의 수집 항목 및 방법)
                        </h2>
                        <p className="mb-4">
                            Komission(이하 &quot;회사&quot;)은 서비스 제공을 위해 다음과 같은 개인정보를 수집합니다:
                        </p>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            <h3 className="font-bold text-white mb-3">필수 수집 항목</h3>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                                <li>이메일 주소 (Google OAuth 연동 시)</li>
                                <li>프로필 이름 및 프로필 이미지</li>
                                <li>서비스 이용 기록 및 접속 로그</li>
                            </ul>
                            <h3 className="font-bold text-white mb-3 mt-6">선택 수집 항목</h3>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                                <li>위치 정보 (O2O 캠페인 참여 시)</li>
                                <li>연락처 정보 (리워드 지급 및 이벤트 당첨 시)</li>
                            </ul>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제2조 (개인정보의 수집 및 이용 목적)
                        </h2>
                        <p className="mb-4">회사는 수집한 개인정보를 다음의 목적으로 이용합니다:</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li><strong className="text-white">회원 관리:</strong> 회원 식별, 가입 의사 확인, 불량 회원 부정 이용 방지</li>
                            <li><strong className="text-white">서비스 제공:</strong> 바이럴 분석 결과 제공, 콘텐츠 계보 추적, 맞춤형 추천</li>
                            <li><strong className="text-white">포인트/로열티 관리:</strong> K-Point 적립·사용 내역 관리, 리워드 지급</li>
                            <li><strong className="text-white">마케팅 및 이벤트:</strong> 신규 기능 안내, 이벤트 정보 제공 (동의 시)</li>
                            <li><strong className="text-white">서비스 개선:</strong> 이용 통계 분석, AI 모델 개선을 위한 익명화 데이터 활용</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제3조 (개인정보의 보유 및 이용 기간)
                        </h2>
                        <p className="mb-4">
                            회사는 개인정보 수집 및 이용 목적이 달성된 후에는 해당 정보를 지체 없이 파기합니다.
                            단, 관련 법령에 따라 보존할 필요가 있는 경우 아래와 같이 보관합니다:
                        </p>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10 space-y-3 text-sm">
                            <div className="flex justify-between">
                                <span>계약 또는 청약철회 등에 관한 기록</span>
                                <span className="text-white font-bold">5년</span>
                            </div>
                            <div className="flex justify-between">
                                <span>대금결제 및 재화 등의 공급에 관한 기록</span>
                                <span className="text-white font-bold">5년</span>
                            </div>
                            <div className="flex justify-between">
                                <span>소비자의 불만 또는 분쟁처리에 관한 기록</span>
                                <span className="text-white font-bold">3년</span>
                            </div>
                            <div className="flex justify-between">
                                <span>웹사이트 방문 기록 (로그 데이터)</span>
                                <span className="text-white font-bold">3개월</span>
                            </div>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제4조 (개인정보의 제3자 제공)
                        </h2>
                        <p className="mb-4">
                            회사는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다.
                            다만, 다음의 경우에는 예외로 합니다:
                        </p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>이용자가 사전에 동의한 경우</li>
                            <li>법령의 규정에 의거하거나, 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우</li>
                            <li>O2O 파트너 브랜드에게 캠페인 참여 확인 정보 제공 (최소한의 정보만 제공)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제5조 (개인정보의 안전성 확보 조치)
                        </h2>
                        <p className="mb-4">회사는 개인정보의 안전성 확보를 위해 다음과 같은 조치를 취하고 있습니다:</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li><strong className="text-white">데이터 암호화:</strong> 전송 중 및 저장 시 AES-256 암호화 적용</li>
                            <li><strong className="text-white">접근 제한:</strong> 개인정보 처리 직원의 최소화 및 접근 권한 관리</li>
                            <li><strong className="text-white">보안 프로그램:</strong> 해킹, 악성코드 방지를 위한 보안 시스템 운영</li>
                            <li><strong className="text-white">정기 점검:</strong> 개인정보 처리 시스템 취약점 정기 점검</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제6조 (이용자의 권리와 행사 방법)
                        </h2>
                        <p className="mb-4">이용자는 언제든지 다음의 권리를 행사할 수 있습니다:</p>
                        <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>개인정보 열람 요청</li>
                            <li>오류 등이 있을 경우 정정 요청</li>
                            <li>삭제 요청 (단, 법령에 따른 보관 의무가 있는 경우 제외)</li>
                            <li>처리 정지 요청</li>
                        </ul>
                        <p className="mt-4 text-white/50 text-sm">
                            ※ 권리 행사는 서비스 내 &apos;마이페이지 → 계정 설정&apos;에서 직접 처리하거나,
                            고객센터(support@komission.ai)로 문의해 주세요.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제7조 (쿠키의 사용)
                        </h2>
                        <p>
                            회사는 이용자에게 개인화된 서비스를 제공하기 위해 쿠키(Cookie)를 사용합니다.
                            쿠키는 웹사이트 운영에 이용되는 서버가 이용자의 브라우저에 보내는 아주 작은 텍스트 파일로,
                            이용자의 컴퓨터 하드디스크에 저장됩니다. 이용자는 브라우저 설정을 통해 쿠키 수신을 거부하거나,
                            쿠키가 저장될 때마다 경고를 받도록 설정할 수 있습니다.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제8조 (개인정보 보호책임자)
                        </h2>
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            <p className="mb-4">
                                회사는 개인정보 처리에 관한 업무를 총괄해서 책임지고, 이용자의 불만처리 및 피해구제 등을
                                위하여 아래와 같이 개인정보 보호책임자를 지정하고 있습니다:
                            </p>
                            <div className="space-y-2 text-sm">
                                <p><strong className="text-white">개인정보 보호책임자:</strong> Komission Privacy Team</p>
                                <p><strong className="text-white">이메일:</strong> privacy@komission.ai</p>
                                <p><strong className="text-white">전화:</strong> 02-0000-0000</p>
                            </div>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <span className="w-1 h-6 bg-pink-500 rounded-full" />
                            제9조 (개인정보처리방침의 변경)
                        </h2>
                        <p>
                            본 개인정보처리방침은 2024년 12월 23일부터 적용됩니다.
                            법령 및 방침에 따른 변경 내용의 추가, 삭제 및 정정이 있는 경우에는
                            변경 사항의 시행 7일 전부터 서비스 내 공지사항 또는 이메일을 통해 고지할 것입니다.
                        </p>
                    </section>

                    {/* Footer */}
                    <div className="pt-10 border-t border-white/10">
                        <div className="flex flex-wrap gap-4 text-sm">
                            <Link href="/terms" className="text-white/40 hover:text-white transition-colors">
                                이용약관 →
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
