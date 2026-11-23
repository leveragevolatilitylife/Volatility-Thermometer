#!/usr/bin/env python3
"""每日 10:00 ET 時段記錄後，用 ntfy.sh 推播三個策略的持倉到手機／電腦。
環境變數 NTFY_TOPIC 未設定就略過；用 data/notified.txt 記錄已推播日期，避免重複。
用法: python scripts/notify.py [--dry] [--date YYYY-MM-DD] [--slot 10:00]"""
import csv, os, sys, json, urllib.request, argparse
ap = argparse.ArgumentParser(); ap.add_argument('--dry', action='store_true')
ap.add_argument('--date'); ap.add_argument('--slot', default='10:00'); a = ap.parse_args()
LOG, DONE = 'data/log.csv', 'data/notified.txt'
rows = list(csv.DictReader(open(LOG, encoding='utf8')))
done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
cand = [r for r in rows if r['slot'] == a.slot and (not a.date or r['date'] == a.date)]
if not cand: print('no slot row'); sys.exit(0)
r = cand[-1]
latest = max(x['date'] for x in rows)
if not a.date and r['date'] != latest: print('slot row is not from latest day; skip'); sys.exit(0)
if r['date'] in done and not a.dry: print('already notified', r['date']); sys.exit(0)
NAME = {'CASH': 'Cash'}
def f(x): return NAME.get(x, x) or '—'
def pct(x):
    try: return f"{float(x)*100:.1f}%"
    except Exception: return '—'
late = r.get('late') in ('1', 'True', 'true')
title = f"{r['date']} {a.slot} ET 持倉"
msg = (f"Defensive：{f(r['defensive'])}\nTactical：{f(r['tactical'])}\nTail：{f(r['tail'])}\n"
       f"Barometer {pct(r['barometer'])}（覆蓋率 {pct(r['coverage'])}）")
if late: msg += "\n⚠ 此時段為延遲補記，價格可能已偏離 10:00"
print(title); print(msg)
topic = os.environ.get('NTFY_TOPIC', '').strip()
if a.dry or not topic: print('(dry-run or NTFY_TOPIC not set — nothing sent)'); sys.exit(0)
body = json.dumps({'topic': topic, 'title': title, 'message': msg, 'priority': 4, 'tags': ['chart_with_upwards_trend']}).encode()
req = urllib.request.Request('https://ntfy.sh/', data=body, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req, timeout=20).read()
open(DONE, 'a').write(r['date'] + '\n'); print('sent')
