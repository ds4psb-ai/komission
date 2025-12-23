// frontend/src/app/remix/[nodeId]/loading.tsx

export default function RemixLoading() {
    return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
                <div className="w-12 h-12 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-white/60 text-sm">로딩 중...</p>
            </div>
        </div>
    );
}
