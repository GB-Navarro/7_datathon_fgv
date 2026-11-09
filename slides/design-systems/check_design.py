"""Browser QA and export for the visual studies; requires optional Playwright."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIEWS = HERE / "previews"
PREVIEWS.mkdir(exist_ok=True)
DATA = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))
TOKENS = json.loads((HERE / "tokens.json").read_text(encoding="utf-8"))

MEASURE = r"""() => {
 const slide=document.querySelector('.slide-shell.is-active .slide');
 const frame=slide.getBoundingClientRect();
 const scale=frame.width/1280;
 const texts=[];
 const canvas=document.createElement('canvas');
 const ctx=canvas.getContext('2d');
 const walker=document.createTreeWalker(slide,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()) {
   const node=walker.currentNode;
   if(!node.textContent.trim()||node.parentElement.closest('svg'))continue;
   const range=document.createRange();range.selectNodeContents(node);
   const style=getComputedStyle(node.parentElement);
   ctx.font=`${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
   const metrics=ctx.measureText(node.textContent.trim());
   const inkOffset=metrics.fontBoundingBoxAscent-metrics.actualBoundingBoxAscent;
   const inkHeight=metrics.actualBoundingBoxAscent+metrics.actualBoundingBoxDescent;
   for(const box of range.getClientRects()) {
     if(!box.width||!box.height)continue;
     texts.push({text:node.textContent.trim().slice(0,90),
       x:(box.left-frame.left)/scale,y:(box.top-frame.top)/scale+inkOffset,
       w:box.width/scale,h:inkHeight,
       block:node.parentElement.closest('h1,h2,p,footer,aside,.chip')?.tagName||node.parentElement.tagName});
   }
 }
 const out=texts.filter(r=>r.x<-.5||r.y<-.5||r.x+r.w>1280.5||r.y+r.h>720.5);
 const overlaps=[];
 for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++) {
   const a=texts[i],b=texts[j];
   const ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x);
   const iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
   if(ix>5&&iy>5&&ix*iy>Math.min(a.w*a.h,b.w*b.h)*.16)
     overlaps.push([a,b]);
 }
 return {out_of_canvas:out,text_overlaps:overlaps};
}"""


def contrast(a: str, b: str) -> float:
    def luminance(h: str) -> float:
        values = [int(h[i:i+2], 16) / 255 for i in (1,3,5)]
        values = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
        return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))
    l1,l2=sorted([luminance(a),luminance(b)])
    return round((l2+.05)/(l1+.05),2)


def main() -> None:
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"Local HTML design studies; glyph ink bounds, controls, claims and print export. SVG geometry and overall composition also require visual inspection.","directions":{},"contrast":{}}
    chrome=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=str(chrome) if chrome.exists() else None,headless=True)
        context=browser.new_context(viewport={"width":1440,"height":910},device_scale_factor=1,reduced_motion='reduce',offline=True)
        for theme in ['aureo','vertice','meridiano']:
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto((HERE/TOKENS[theme]['file']).as_uri())
            page.evaluate('document.fonts.ready')
            assert page.locator('.slide-shell').count()==8
            font_status=page.evaluate("[...document.fonts].map(f=>({family:f.family,status:f.status})).filter(f=>f.status==='loaded')")
            slides=[]
            for i in range(8):
                if i: page.locator('[data-next]').click()
                assert page.locator('[data-counter]').inner_text().startswith(f'{i+1:02d}')
                claims=page.locator('.is-active [data-claim]').evaluate_all('(nodes)=>nodes.map(n=>({key:n.dataset.claim,raw:Number(n.dataset.raw)}))')
                assert all(abs(DATA[c['key']]-c['raw'])<1e-8 for c in claims)
                layout=page.evaluate(MEASURE)
                slides.append({"slide":i+1,**layout,"verified_claim_instances":len(claims)})
                page.locator('.slide-shell.is-active').screenshot(path=str(PREVIEWS/f'{theme}-{i+1:02d}.png'))
                if i==0:page.locator('.slide-shell.is-active').screenshot(path=str(PREVIEWS/f'{theme}-cover.png'))
            page.keyboard.press('Home');assert page.locator('[data-counter]').inner_text().startswith('01')
            assert page.locator('[data-prev]').is_disabled()
            page.keyboard.press('ArrowRight');assert page.locator('[data-counter]').inner_text().startswith('02')
            page.keyboard.press('End');assert page.locator('[data-next]').is_disabled()
            page.locator('[data-overview]').click();assert page.locator('body').evaluate("b=>b.classList.contains('is-overview')")
            page.locator('.slide-shell').nth(3).click();assert page.locator('[data-counter]').inner_text().startswith('04')
            assert not page.locator('body').evaluate("b=>b.classList.contains('is-overview')")
            page.locator('[data-help]').click();assert page.locator('dialog').evaluate('d=>d.open')
            page.locator('[data-close-help]').click()
            page.locator('[data-fullscreen]').click();page.wait_for_function('Boolean(document.fullscreenElement)')
            page.keyboard.press('f');page.wait_for_function('!document.fullscreenElement')
            page.pdf(path=str(PREVIEWS/f'{theme}.pdf'),print_background=True,prefer_css_page_size=True)
            responsive=[]
            for width,height in [(1920,1080),(1024,768),(390,844)]:
                page.set_viewport_size({"width":width,"height":height})
                page.wait_for_timeout(70)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                responsive.append({"viewport":[width,height],"horizontal_overflow":False})
            report['directions'][theme]={"slides":slides,"loaded_fonts":font_status,"javascript_errors":errors,"keyboard_and_controls":"passed","offline_file_open":"passed","responsive":responsive}
            css=(HERE/f'assets/{theme}.css').read_text(encoding='utf-8')
            variables=dict(re.findall(r'--([a-z-]+):(#\w{6})',css))
            pairs={}
            for role in ['paper','gold','muted','reference','negative']:
                pairs[f'{role}_on_dark']=contrast(variables[role],variables['bg'])
            for role in ['bg','light-muted','light-gold','light-ref','light-negative']:
                pairs[f'{role}_on_paper']=contrast(variables[role],variables['paper'])
            if theme=='aureo':
                pairs['ink_on_gold']=contrast(variables['bg'],variables['gold'])
                # The identity sheet must show the actual five token colors.
                swatch_colors=page.locator('.a-ink-sample').evaluate_all('(nodes)=>nodes.map(n=>getComputedStyle(n).backgroundColor)')
                expected=[TOKENS['aureo']['colors'][key] for key in ['background','paper','gold','reference','negative']]
                expected_rgb=['rgb('+', '.join(str(int(color[i:i+2],16)) for i in (1,3,5))+')' for color in expected]
                assert swatch_colors==expected_rgb
                report['directions'][theme]['palette_matches_tokens']=True
            report['contrast'][theme]=pairs
            page.close()
        page=context.new_page()
        page.goto((HERE/'index.html').as_uri());page.evaluate('document.fonts.ready')
        assert page.locator('.direction').count()==3
        assert page.locator('img').evaluate_all('(images)=>images.every(img=>img.complete&&img.naturalWidth>0)')
        page.screenshot(path=str(PREVIEWS/'biblioteca.png'),full_page=True)
        for width in [1024,390]:
            page.set_viewport_size({"width":width,"height":844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        report['library']={'three_directions':True,'all_cover_images_loaded':True,'mobile_horizontal_overflow':False}
        browser.close()
    import pymupdf as fitz
    for theme in ['aureo','vertice','meridiano']:
        with fitz.open(PREVIEWS/f'{theme}.pdf') as pdf:
            assert len(pdf)==8
            assert all(abs(p.rect.width-960)<1 and abs(p.rect.height-540)<1 for p in pdf)
            report['directions'][theme]['pdf_pages']=len(pdf)
    report['status']='passed' if all(not s['out_of_canvas'] and not s['text_overlaps'] for t in report['directions'].values() for s in t['slides']) and all(v>=4.5 for t in report['contrast'].values() for v in t.values()) and all(not t['javascript_errors'] for t in report['directions'].values()) else 'needs_review'
    (HERE/'QA_design.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'layout_findings':{theme:[s for s in item['slides'] if s['out_of_canvas'] or s['text_overlaps']] for theme,item in report['directions'].items()},'contrast':report['contrast']},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
