#!/usr/bin/env python3
"""Additional library checks: coverage, reachability, assets and editorial completeness."""
import json,re,sys,collections,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from check import PAGES,Page,ROOT
routes=json.loads((ROOT/'editorial/routes.json').read_text())
errors=[]; graph={}; words=[]; prompts=set(); slugs=set()
for route,path in PAGES.items():
 s=(ROOT/path).read_text();p=Page(s)
 graph[route]={urlsplit(u).path or route for u in p.links if not urlsplit(u).scheme and not urlsplit(u).netloc}
 if route in routes:
  if not p.header or not p.footer:errors.append(route+': missing navigation')
  if route.count('/')==3 and route.split('/')[2] not in ('briefs','story','visual','narration','workflows','review','publishing','free'):
   for anchor in ['method','brief','review','sources']:
    if anchor not in p.ids:errors.append(route+': missing '+anchor)
   if 'Written illustration of this method' not in s:errors.append(route+': missing example scope')
for source in (ROOT/'editorial').glob('*.txt'):
 for line in source.read_text().splitlines():
  if not line:continue
  parts=line.split('|')
  if len(parts)!=7:errors.append(str(source)+': malformed record');continue
  slug,title,answer,steps,example,checks,pitfall=parts
  if slug in slugs:errors.append(slug+': duplicate slug')
  if example in prompts:errors.append(slug+': duplicate example')
  slugs.add(slug);prompts.add(example)
  if len(steps.split('~'))!=3 or len(checks.split('~'))!=3:errors.append(slug+': incomplete checklist')
  if not (ROOT/f'guides/worksheets/{slug}.txt').exists():errors.append(slug+': missing worksheet')
  words.append(len(' '.join(parts[1:]).replace('~',' ').split()))
seen={'/'}; q=collections.deque(['/'])
while q:
 for nxt in graph[q.popleft()]:
  if nxt in graph and nxt not in seen:seen.add(nxt);q.append(nxt)
for r in PAGES:
 if r not in seen:errors.append(r+': unreachable from home')
if len(routes)!=90 or len(PAGES)!=107 or len(prompts)!=81:errors.append('Unexpected inventory; update the explicit delivery expectation when adding pages.')
print(json.dumps({'pages':len(PAGES),'new_pages':len(routes),'authored_guides':len(prompts),'worksheets':len(list((ROOT/'guides/worksheets').glob('*.txt'))),'unique_editorial_words_min':min(words),'unique_editorial_words_total':sum(words),'reachable_from_home':len(seen),'errors':errors},indent=2))
sys.exit(bool(errors))
