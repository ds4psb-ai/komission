#!/usr/bin/env python3
"""VDG Pipeline Test Script for goodworkmb video"""

import json
import sys
import traceback
from app.services.vdg_2pass.vdg_unified_pipeline import VDGUnifiedPipeline, PipelineConfig

video_path = '/Users/ted/komission/exports/vdg_consulting/videos/goodworkmb_7581925214062136590.mp4'
top_comments = [
    'And in the end itll all be bought by Disney',
    'Brought to you by EVERYONE',
    'DJ MUSTARD',
    'The Shrek transition had me weak',
    'PAKISTAN PICTURES'
]

def main():
    print('=== VDG Pipeline Test ===', flush=True)
    
    config = PipelineConfig(
        skip_cv_pass=True,
        media_resolution='low'
    )
    
    print(f'Video: {video_path}', flush=True)
    
    try:
        pipeline = VDGUnifiedPipeline(config=config)
        print('Pipeline initialized', flush=True)
        
        result = pipeline.run(
            video_path=video_path,
            platform='tiktok',
            caption='every company is every company',
            hashtags=['business', 'news', 'netflix'],
            top_comments=top_comments,
        )
        
        print(f'LLM Output received', flush=True)
        print(f'Scenes count: {len(result.llm_output.scenes)}', flush=True)
        print(f'Capsule brief shotlist: {len(result.llm_output.capsule_brief.shotlist)}', flush=True)
        print(f'Capsule brief do_not: {len(result.llm_output.capsule_brief.do_not)}', flush=True)
        print(f'Viral kicks: {len(result.llm_output.viral_kicks)}', flush=True)
        
        # Export
        output = result.llm_output.model_dump()
        output_path = '/Users/ted/komission/exports/vdg_consulting/goodworkmb_7581925214062136590_llm_output.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'Exported to: {output_path}', flush=True)
        
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}', flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
