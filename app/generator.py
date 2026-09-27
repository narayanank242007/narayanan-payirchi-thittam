import os, uuid, re, json
from pathlib import Path
from fpdf import FPDF

BASE=Path(__file__).resolve().parent.parent
PANELS=BASE/"static/panels"; EXPORTS=BASE/"static/exports"
PANELS.mkdir(parents=True,exist_ok=True); EXPORTS.mkdir(parents=True,exist_ok=True)

def demo(prompt, character, setting, tone, style):
    titles=["The Spark","Into the Unknown","The Turning Point","A Bold Choice","The New Dawn"]
    beats=[f"{character} discovers an unexpected clue in {setting}.",f"The clue pulls {character} deeper into the world around them.",f"A surprising obstacle forces {character} to rethink the plan.",f"With courage and creativity, {character} makes a decisive move.",f"The journey ends with a discovery and a new beginning."]
    return [{"number":i+1,"title":titles[i],"scene":beats[i],"image_prompt":f"{style} comic panel, {setting}, {character}, {beats[i]}, {tone} mood","caption":f"SCENE {i+1} • {tone.upper()}","narration":f"{character} faces the moment with determination.","dialogue":"We keep moving. There has to be a way forward."} for i in range(5)]

def outline(prompt,character,setting,tone,style):
    key=os.getenv("GEMINI_API_KEY")
    if not key: return demo(prompt,character,setting,tone,style)
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        m=genai.GenerativeModel("gemini-1.5-flash")
        r=m.generate_content(f"Create exactly 5 comic panels as JSON array. Prompt:{prompt}; Character:{character}; Setting:{setting}; Tone:{tone}; Art:{style}. Each item: number,title,scene,image_prompt. JSON only.")
        return json.loads(r.text.replace("```json","").replace("```","").strip())[:5]
    except Exception: return demo(prompt,character,setting,tone,style)

def enrich(panels,character,tone):
    key=os.getenv("GEMINI_API_KEY")
    if not key: return panels
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        m=genai.GenerativeModel("gemini-1.5-pro")
        r=m.generate_content(f"Add short caption,narration,dialogue to these panels. Character={character}, tone={tone}. JSON only. {json.dumps(panels)}")
        data=json.loads(r.text.replace("```json","").replace("```","").strip())
        for i,x in enumerate(data[:5]): panels[i].update({k:x.get(k,"") for k in ["caption","narration","dialogue"]})
    except Exception: pass
    return panels

def panel_image(panel,style):
    fn=f"panel_{panel['number']}_{uuid.uuid4().hex[:8]}.svg"
    clean=lambda x:re.sub(r"[^A-Za-z0-9 .,!?'_-]","",str(x))
    title=clean(panel.get("title","Panel")); scene=clean(panel.get("scene",""))[:140]
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760"><defs><linearGradient id="g"><stop stop-color="#161a33"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs><rect width="1200" height="760" fill="url(#g)"/><circle cx="930" cy="170" r="180" fill="#f59e0b" opacity=".22"/><circle cx="250" cy="600" r="260" fill="#22d3ee" opacity=".12"/><text x="80" y="120" fill="white" font-family="Arial" font-size="28" font-weight="bold">COMICFORGE PANEL {panel['number']}</text><text x="80" y="260" fill="white" font-family="Arial" font-size="64" font-weight="bold">{title}</text><text x="80" y="350" fill="#f8fafc" font-family="Arial" font-size="30">{scene}</text><text x="80" y="690" fill="#cbd5e1" font-family="Arial" font-size="22">{clean(style)}</text></svg>'''
    (PANELS/fn).write_text(svg,encoding="utf-8")
    return "/static/panels/"+fn

def pdf_export(panels):
    fn=f"comicforge_{uuid.uuid4().hex[:10]}.pdf"; path=EXPORTS/fn
    pdf=FPDF(); pdf.set_auto_page_break(True,15)
    for p in panels:
        pdf.add_page(); pdf.set_font("Helvetica","B",20); pdf.cell(0,12,f"Panel {p['number']}: {p.get('title','')}",ln=True); pdf.ln(4); pdf.set_font("Helvetica","",12)
        for k in ["scene","caption","narration","dialogue"]:
            if p.get(k): pdf.multi_cell(0,7,str(p[k])); pdf.ln(2)
    pdf.output(str(path)); return "/static/exports/"+fn

def build_comic(prompt,character,setting,tone,style):
    panels=enrich(outline(prompt,character,setting,tone,style),character,tone)
    for p in panels: p["image"]=panel_image(p,style)
    return panels,pdf_export(panels)
