#!/usr/bin/env python3
"""Build the authored Kleo production library. Standard library only; no API or paid render.
Edit editorial/*.txt, then run this script and tools/sitemap.py. Does not touch DNS or the MCP service.
"""
from pathlib import Path
import html,json,re,csv
ROOT=Path(__file__).resolve().parent.parent
BASE='https://kleooai.com'
REVIEWED='2026-09-23'
e=lambda v:html.escape(str(v),quote=True)
GROUPS={
 'briefs':('Video briefs','Turn an idea into an approved production brief.','A useful brief gives the production conversation a decision to make. Start with the viewer, the question and the intended ending. The guides here cover different inputs to that decision: factual evidence, visual references, client requirements and revision history. Use the downloadable worksheet on each guide to record your own choices. These are editorial methods, not promises that a prompt will control every generated detail.','Audience','Question','Treatment','Approval'),
 'story':('Story and structure','Build a story viewers can follow from opening to ending.','Story planning is about relationships between events. Start with the guide matching your actual problem: an unclear opening, disconnected scenes, an arbitrary ending or a series with overlapping episodes. The fictional examples demonstrate a planning technique; they are not claims about films already rendered by Kleo. Review the treatment as a whole before approving production, because an attractive individual shot cannot supply a missing cause or consequence.','Situation','Change','Consequence','Ending'),
 'visual':('Visual direction','Direct framing, continuity and the look of generated scenes.','Visual direction translates the story into visible choices. Begin with what the viewer must notice, then choose framing, movement and lighting that make it legible. Generated footage requires inspection: writing a continuity rule or a camera instruction does not prove the result follows it. These guides explain what to request and what to check. Use the public examples to understand the current presentation, and the actual downloaded result to judge your own project.','Subject','Framing','Movement','Review'),
 'narration':('Narration and language','Prepare clear narration and review the actual audio.','A narration draft has to work when heard once, at the pace of the pictures. Start with meaning and factual accuracy before adjusting tone. Kleo currently advertises one narrator in English or Italian; check the current options before promising another language or multiple acted voices. The guides separate writing decisions from audio verification. A script can look correct while its generated delivery contains a mispronounced name, a lost word or an awkward pause.','Meaning','Script','Delivery','Listening'),
 'workflows':('Production workflows','Move from planning to a reviewed, saved video deliverable.','A clear workflow records decisions before a render and checks the result afterward. Kleo connects to an assistant through MCP, while the assistant presents the treatment, tools and result. Keep the approved creative version separate from the job identifier and quote. The guides in this section address different operational decisions, from choosing an animatic to archiving the final MP4. Product availability and quoted costs should be confirmed at the time of production.','Plan','Approve','Render','Save'),
 'review':('Quality review','Check the film, its evidence and the complete release package.','Quality review needs several focused passes rather than one impression of whether a film looks good. Check facts, story clarity, visual continuity, audio and publication materials separately. Give every issue a timestamp or source reference and assign a person to resolve it. These guides are practical editorial checklists, not certifications of legal clearance, accessibility conformance or factual accuracy. The relevant reviewer must inspect the actual final deliverable, not only the intended prompt.','Evidence','Picture','Sound','Sign-off'),
 'publishing':('Publishing and discovery','Prepare accurate titles, captions, sources and platform uploads.','Publishing is part of the production process. The title, thumbnail and description create expectations that the film must meet. Keep source links and credits traceable, and check the destination platform’s current requirements before upload. Kleo’s public workflow supplies a downloadable result; you decide what to publish and when. The guides here distinguish practical editorial advice from platform rules, with links to official guidance where a rule is discussed.','File','Metadata','Preview','Publish'),
 'free':('Free AI video resources','Understand the starter offer and plan before buying credits.','Free is useful only when the offer is clear. Kleo currently provides seven starter credits after connecting, and an animatic costs five credits. Its generated-footage film requires a pack purchase. This section separates the free starting experience, story planning and the choice to move to paid production. Check the current pricing before authorizing a job. Any assistant you connect may have its own access conditions, which are separate from Kleo’s production credits.','Connect','7 credits','Animatic','Review')}
EXTERNAL={
 'youtube-upload-checklist':[('YouTube: upload videos','https://support.google.com/youtube/answer/57407?hl=en','Current upload workflow; check the platform again before publishing.')],
 'youtube-shorts-format':[('YouTube: three-minute Shorts','https://support.google.com/youtube/answer/15424877?hl=en','Current duration and aspect-ratio classification; music and rights conditions must be reviewed separately.')],
 'caption-handoff':[('W3C WAI: captions and subtitles','https://www.w3.org/WAI/media/av/captions/','Caption purpose, accuracy and timing; a checklist alone does not establish conformance.')],
 'ai-disclosure':[('YouTube: altered or synthetic content','https://support.google.com/youtube/answer/14328491?hl=en','Platform disclosure guidance for the actual finished content.')],
 'reconstruction-labels':[('YouTube: altered or synthetic content','https://support.google.com/youtube/answer/14328491?hl=en','Disclosure guidance complements clear editorial labeling.')],
 'assistant-handoff':[('MCP: architecture overview','https://modelcontextprotocol.io/docs/learn/architecture','Background on the host, client and server model; not a guarantee that conversation history moves between hosts.')],
}
source=(ROOT/'ai-youtube-video-generator/index.html').read_text()
head=source[:source.index('<body>')]
nav=re.search(r'<nav class="nav".*?</nav>',source,re.S).group().replace(' aria-current="page"','')
footer=re.search(r'<footer.*?</footer>',source,re.S).group()
# Add one library link consistently to the existing site footer, retaining every old destination.
if 'href="/guides/"' not in footer:
 footer=footer.replace('<a href="/faq/">FAQ</a>','<a href="/faq/">FAQ</a>\n      <a href="/guides/">Guides</a>')
assert 'href="/guides/"' in footer
for p in ROOT.rglob('*.html'):
 if '.git' in p.parts:continue
 t=p.read_text(); t=re.sub(r'<footer.*?</footer>',lambda _:footer,t,flags=re.S);p.write_text(t)
articles=[]
for group in GROUPS:
 for line in (ROOT/'editorial'/f'{group}.txt').read_text().splitlines():
  if not line.strip():continue
  fields=line.split('|');assert len(fields)==7,(group,len(fields))
  slug,title,answer,steps,example,checks,pitfall=fields
  articles.append(dict(group=group,slug=slug,title=title,answer=answer,steps=steps.split('~'),example=example,checks=checks.split('~'),pitfall=pitfall,route=f'/guides/{slug}/'))
assert len(articles)==81
assert len({a['slug'] for a in articles})==81
routes={}
manifest=[]
css='''/* Scoped additions for the production guide library; existing pages retain their layout. */
.guide-body{max-width:78ch;margin-inline:auto}.guide-body h2{font-size:clamp(1.65rem,3vw,2.2rem);margin:44px 0 18px}.guide-body h2:first-child{margin-top:0}.guide-body .panel{margin:24px 0}.guide-body li{margin-bottom:12px}.guide-body .style-say{font-size:1rem;line-height:1.75}.guide-diagram{display:block;width:100%;height:auto;border-radius:18px;margin:26px 0}.guide-meta{color:var(--mute);font-size:.875rem;margin-top:18px}.guide-toc{display:flex;flex-wrap:wrap;gap:10px 22px;margin-top:22px}.guide-toc a,.guide-body a{text-decoration:underline;text-underline-offset:3px}.guide-body a:hover{color:var(--amber)}.guide-body .btn{text-decoration:none}.guide-cards .panel h2{font-size:1.35rem}.guide-cards .panel p{line-height:1.65}.guide-body pre{white-space:pre-wrap;overflow-wrap:anywhere}.guide-body ul{padding-left:24px}@media(max-width:600px){.guide-body .panel{padding:20px 18px}.guide-toc{display:grid;gap:12px}.guide-diagram{border-radius:12px}}
'''
(ROOT/'guides').mkdir(exist_ok=True)
(ROOT/'guides/library.css').write_text(css)
(ROOT/'guides/media').mkdir(exist_ok=True)
(ROOT/'guides/worksheets').mkdir(exist_ok=True)
for g,data in GROUPS.items():
 labels=data[3:]
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="520" viewBox="0 0 1000 520" role="img">',f'<title>{e(data[0])}: four planning stages</title>','<rect width="1000" height="520" rx="28" fill="#10141b"/>',f'<text x="52" y="66" fill="#ffc277" font-family="sans-serif" font-size="22">KLEO / {e(data[0].upper())}</text>']
 for i,label in enumerate(labels):
  x=52+(i%2)*460;y=105+(i//2)*184
  parts += [f'<rect x="{x}" y="{y}" width="436" height="154" rx="20" fill="#1b222c" stroke="#3e4857"/>',f'<text x="{x+26}" y="{y+48}" fill="#ffc277" font-family="monospace" font-size="25">0{i+1}</text>',f'<text x="{x+26}" y="{y+103}" fill="#f4f1eb" font-family="sans-serif" font-size="32">{e(label)}</text>']
 parts.append('</svg>');(ROOT/f'guides/media/{g}.svg').write_text('\n'.join(parts))
def link(route,label):return f'<a href="{e(route)}">{e(label)}</a>'
def page(route,title,desc,answer,body,crumbs,extra=None):
 title=title+' | Kleo';desc=desc if len(desc)<=165 else desc[:162].rsplit(' ',1)[0]+'.'
 h=re.sub(r'<title>.*?</title>',f'<title>{e(title)}</title>',head,flags=re.S)
 for attr,key,val in [('name','description',desc),('property','og:title',title),('property','og:description',desc),('property','og:url',BASE+route),('name','twitter:title',title),('name','twitter:description',desc)]:
  h=re.sub(r'<meta '+attr+'="'+key+r'" content="[^"]*">',f'<meta {attr}="{key}" content="{e(val)}">',h)
 h=re.sub(r'<link rel="canonical" href="[^"]*">',f'<link rel="canonical" href="{BASE+route}">',h)
 graph=[{'@type':'WebSite','@id':BASE+'/#website','name':'Kleo AI','url':BASE+'/'},{'@type':'WebPage','@id':BASE+route+'#page','url':BASE+route,'name':title,'description':desc,'inLanguage':'en','isPartOf':{'@id':BASE+'/#website'}},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':BASE+r} for i,(name,r) in enumerate(crumbs)]}]
 if extra:graph.extend(extra)
 ld=json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,indent=2).replace('</','<\\/')
 h=re.sub(r'<script type="application/ld\+json">.*?</script>',lambda _:f'<script type="application/ld+json">\n{ld}\n</script>',h,flags=re.S)
 h=h.replace('</head>','<link rel="stylesheet" href="/guides/library.css">\n</head>')
 crumb=' <span aria-hidden="true">›</span> '.join(link(r,n) for n,r in crumbs[:-1])+f' <span aria-hidden="true">›</span> <span>{e(crumbs[-1][0])}</span>'
 out=h+f'''<body>
<div class="progress" id="progress" aria-hidden="true"></div>
{nav}
<main id="main">
<section class="page-hero hero"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb">{crumb}</nav>
<h1>{e(title[:-7])}</h1><p class="lede">{e(answer)}</p>
<p class="guide-meta">Kleo production guides · English · Editorial review {REVIEWED}</p>
<div class="cta-row"><a class="btn btn-primary" href="/connect/">Connect Kleo</a><a class="btn btn-ghost" href="/pricing/">Check current pricing</a></div>
</div></section>
{body}
</main>
{footer}
<div class="toast" id="toast" role="status" aria-live="polite">Copied</div>
</body></html>'''
 path=route.strip('/')+'/index.html';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(out)
 routes[route]=path
 manifest.append({'route':route,'title':title,'description':desc,'file':path})
def cards(items):
 return '<div class="grid panels guide-cards">'+''.join(f'<article class="panel"><h2>{link(a[0],a[1])}</h2><p>{e(a[2])}</p></article>' for a in items)+'</div>'
for a in articles:
 g=a['group'];group=GROUPS[g];r=a['route'];slug=a['slug']
 siblings=[x for x in articles if x['group']==g];idx=siblings.index(a)
 related=[siblings[(idx+1)%len(siblings)],siblings[(idx+2)%len(siblings)]]
 # Add a meaningful cross-stage link in addition to the adjacent subject guides.
 cross={'briefs':'treatment-approval','story':'storyboard-density','visual':'visual-artifact-review','narration':'audio-review','workflows':'brief-compliance','review':'release-signoff','publishing':'source-pack','free':'film-or-animatic'}[g]
 candidate=next(x for x in articles if x['slug']==cross)
 if candidate!=a and candidate not in related:related.append(candidate)
 refs=[('Kleo FAQ','/faq/','Product capabilities and limitations; reconfirm before production.'),('Kleo pricing','/pricing/','Current starter offer, product conditions and quoted credit costs.')]
 refs+=EXTERNAL.get(slug,[])
 worksheet=f'KLEO PRODUCTION WORKSHEET\n{a["title"]}\nGuide: {BASE+r}\n\nProject:\nVersion:\nReviewer:\n\nDECISIONS\n'+''.join(f'{i+1}. {s}\nYour decision:\n\n' for i,s in enumerate(a['steps']))+'REVIEW\n'+''.join(f'[ ] {s}\nEvidence / timestamp:\n\n' for s in a['checks'])+'PITFALL\n'+a['pitfall']+'\n\nThis worksheet is a planning aid, not a rendered example or automated verification.\n'
 (ROOT/f'guides/worksheets/{slug}.txt').write_text(worksheet)
 body=f'''<section><div class="wrap"><article class="prose guide-body">
<nav class="guide-toc" aria-label="On this page"><a href="#method">Method</a><a href="#brief">Example brief</a><a href="#review">Review checklist</a><a href="#sources">Sources and scope</a></nav>
<img class="guide-diagram" src="/guides/media/{g}.svg" width="1000" height="520" loading="lazy" alt="Planning sequence: {e(', then '.join(group[3:]))}.">
<h2 id="method">A practical method</h2><ol>{''.join('<li>'+e(s)+'</li>' for s in a['steps'])}</ol>
<h2 id="brief">An example brief to adapt</h2><p class="guide-meta">Written illustration of this method; not a report of a rendered film or a customer result.</p>
<div class="panel"><p class="style-say">{e(a['example'])}</p></div>
<h2 id="review">Review before moving on</h2><ul>{''.join('<li>'+e(s)+'</li>' for s in a['checks'])}</ul>
<p>Record a concrete observation beside each check: a line in the treatment, a source passage or a timestamp in the downloaded film. If you cannot inspect an item yet, leave it open. A request in a brief is an intention; the result is what must be reviewed.</p>
<p>{link('/guides/worksheets/'+slug+'.txt','Download this guide’s editable text worksheet')}</p>
<h2>What to avoid</h2><p>{e(a['pitfall'])}</p>
<h2 id="sources">Sources and scope</h2><p>The method and fictional brief are original editorial guidance for planning and review. They do not establish a measured performance gain or guarantee a particular render. Product statements follow Kleo’s public pages, checked on {REVIEWED}; official platform guidance is linked where relevant.</p>
<ul>{''.join('<li>'+link(url,label)+' — '+e(scope)+'</li>' for label,url,scope in refs)}</ul>
<p>{link('/examples/','See the published Kleo examples')} to inspect actual showcased work. Example films may reflect a different production setup; check the current offer for your own job.</p>
<h2>Continue your production plan</h2><ul>{''.join('<li>'+link(x['route'],x['title'])+'</li>' for x in related)}<li>{link('/guides/'+g+'/',group[0]+' — all guides')}</li></ul>
</article></div></section>'''
 extra=[{'@type':'Article','@id':BASE+r+'#article','headline':a['title'],'mainEntityOfPage':{'@id':BASE+r+'#page'},'inLanguage':'en','author':{'@type':'Organization','name':'Kleo AI','url':BASE+'/about/'},'publisher':{'@type':'Organization','name':'Kleo AI','url':BASE+'/'},'citation':[BASE+u if u.startswith('/') else u for _,u,_ in refs]}]
 page(r,a['title'],a['title']+'. A practical Kleo guide with an example brief, clear steps and an editable review worksheet.',a['answer'],body,[('Home','/'),('Guides','/guides/'),(group[0],'/guides/'+g+'/'),(a['title'],r)],extra)
for g,data in GROUPS.items():
 members=[a for a in articles if a['group']==g];r='/guides/'+g+'/'
 content=f'<section><div class="wrap"><div class="prose guide-body"><h2>Choose the decision you need to make</h2><p>{e(data[2])}</p><img class="guide-diagram" src="/guides/media/{g}.svg" width="1000" height="520" alt="{e(", then ".join(data[3:]))}." loading="lazy"></div>'+cards([(a['route'],a['title'],a['answer']) for a in members])+f'<div class="prose guide-body"><h2>Move through the production</h2><p>{link("/guides/","Browse all production topics")} or {link("/ai-youtube-video-generator/","read the complete Kleo workflow")}. Choose guides by the decision at hand, then keep your approved choices with the project.</p></div></div></section>'
 extra=[{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':BASE+a['route'],'name':a['title']} for i,a in enumerate(members)]}]
 page(r,data[0]+' for AI films',data[1]+' Practical briefs, examples and review checklists for the Kleo production workflow.',data[2],content,[('Home','/'),('Guides','/guides/'),(data[0],r)],extra)
items=[('/guides/'+g+'/',d[0],d[1]) for g,d in GROUPS.items()]
body='<section><div class="wrap">'+cards(items)+'''<div class="prose guide-body"><h2>Start with the next useful decision</h2><p>These 81 focused guides cover the work around a narrated AI film: what to ask for, how to structure it, what to inspect and how to publish it responsibly. Each article includes an original example brief and an editable text worksheet. The methods are editorial guidance, not claims of tested performance.</p><h2>What is free?</h2><p>Kleo’s public offer currently includes seven starter credits, enough for one five-credit animatic. A generated-footage film requires a pack purchase. <a href="/guides/free-ai-video-generator/">Read the free starting offer</a> and <a href="/pricing/">check current pricing</a> before authorizing a job.</p><h2>Look at the product itself</h2><p><a href="/examples/">Published examples</a> show existing work. <a href="/connect/">The connection guide</a> explains how to use Kleo with a compatible assistant. <a href="/faq/">The FAQ</a> states current product limits. Do not infer a feature from a fictional brief in this library.</p></div></div></section>'''
page('/guides/','AI filmmaking guides: briefs, stories and publishing','Plan and review AI films with 81 practical Kleo guides: original example briefs, editable checklists, narration, visual direction and publishing advice.','Human direction is a set of decisions. Work through your brief, story, shots, narration, production and release with a guide for the task in front of you.',body,[('Home','/'),('Guides','/guides/')])
# Contextual entrance from the existing main product guide. No old section is removed.
p=ROOT/'ai-youtube-video-generator/index.html';t=p.read_text()
block='''<!-- KLEO_GUIDE_ENTRANCE_START -->
<section id="production-guides"><div class="wrap"><div class="sec-head one"><h2>Plan the details of your film.</h2></div><div class="prose"><p>Use the <a href="/guides/">production guide library</a> for practical briefs, story structure, narration and quality review. Start with <a href="/guides/free-ai-video-generator/">what the free starter offer includes</a>, or <a href="/guides/treatment-approval/">how to approve a treatment</a> before rendering.</p></div></div></section>
<!-- KLEO_GUIDE_ENTRANCE_END -->'''
if '<!-- KLEO_GUIDE_ENTRANCE_START -->' in t:t=re.sub(r'<!-- KLEO_GUIDE_ENTRANCE_START -->.*?<!-- KLEO_GUIDE_ENTRANCE_END -->',lambda _:block,t,flags=re.S)
else:t=t.replace('</main>',block+'\n</main>')
p.write_text(t)
(ROOT/'editorial/routes.json').write_text(json.dumps(routes,indent=2)+'\n')
(ROOT/'editorial/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (ROOT/'editorial/page-inventory.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['route','title','description','file'],lineterminator='\n');w.writeheader();w.writerows(manifest)
print(f'Built {len(articles)} guides, {len(GROUPS)} topic hubs and 1 library = {len(routes)} new pages.')
