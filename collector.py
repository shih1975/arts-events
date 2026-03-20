#!/usr/bin/env python3
"""
台北・新北 藝文活動自動收集器（Gemini 版，免費）
每週日晚上執行，收集未來兩週活動，產出 index.html
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ── 設定 ──────────────────────────────────────────
CITY_FILTER = "台北市、新北市"
MAX_PRICE   = 1000
PRICE_NOTE  = f"費用超過 NT${MAX_PRICE} 不列入"
TZ          = ZoneInfo("Asia/Taipei")
GEMINI_MODEL = "gemini-2.0-flash"   # 免費額度最高的模型

CATEGORIES = [
    {"key": "flower",      "label": "🌸 賞花"},
    {"key": "exhibition",  "label": "🖼️ 展覽"},
    {"key": "workshop",    "label": "🎨 工作坊"},
    {"key": "performance", "label": "🎭 表演"},
    {"key": "market",      "label": "🛍️ 市集"},
    {"key": "music",       "label": "🎵 音樂演出"},
]

CATEGORY_KEYWORDS = {
    "flower":      "賞花、花季、花卉展",
    "exhibition":  "藝術展覽、美術館展、博物館特展、攝影展、設計展",
    "workshop":    "手作課程、工作坊、繪畫課、陶藝課、創作體驗",
    "performance": "舞台劇、舞蹈表演、戲劇演出、音樂劇",
    "market":      "藝文市集、創作市集、手作市集、文創市集",
    "music":       "音樂會、演唱會、樂團演出、音樂節",
}

# ── HTML 樣板 ──────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>台北・新北 藝文活動 {date_range}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500&display=swap');
  :root{{--bg:#faf8f5;--card:#fff;--text:#1a1410;--muted:#6b5c4e;--border:#e8e0d5;--accent:#c0392b}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Noto Sans TC',sans-serif;background:var(--bg);color:var(--text)}}
  .hero{{background:linear-gradient(135deg,#1a0a05,#3d1f0f,#1a0a05);color:#fff;padding:48px 24px 36px;text-align:center}}
  .hero::before{{content:'✦  ✦  ✦';display:block;font-size:10px;letter-spacing:12px;color:rgba(255,255,255,.3);margin-bottom:16px}}
  .hero h1{{font-family:'Noto Serif TC',serif;font-size:clamp(24px,4vw,42px);font-weight:700;letter-spacing:.06em;margin-bottom:8px}}
  .hero .sub{{font-size:13px;color:rgba(255,255,255,.55);letter-spacing:.18em}}
  .hero .badge{{display:inline-block;margin-top:16px;padding:5px 18px;border:1px solid rgba(255,255,255,.22);border-radius:20px;font-size:12px;color:rgba(255,255,255,.75)}}
  .hero .updated{{display:block;margin-top:10px;font-size:11px;color:rgba(255,255,255,.4)}}
  .nav{{background:var(--card);border-bottom:1px solid var(--border);padding:0 20px;display:flex;overflow-x:auto;scrollbar-width:none;position:sticky;top:0;z-index:100;box-shadow:0 2px 6px rgba(0,0,0,.05)}}
  .nav::-webkit-scrollbar{{display:none}}
  .tab{{padding:13px 18px;border:none;background:none;font-size:12.5px;font-family:'Noto Sans TC',sans-serif;color:var(--muted);cursor:pointer;white-space:nowrap;border-bottom:2px solid transparent;transition:all .15s}}
  .tab:hover{{color:var(--text)}}
  .tab.on{{color:var(--text);border-bottom-color:var(--accent);font-weight:500}}
  .wrap{{max-width:980px;margin:0 auto;padding:32px 20px 60px}}
  .sec{{display:none}}.sec.on{{display:block}}
  .sec-head{{display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid var(--border)}}
  .sec-title{{font-family:'Noto Serif TC',serif;font-size:20px;font-weight:600}}
  .cnt{{font-size:11px;color:var(--muted);background:var(--bg);padding:2px 9px;border-radius:10px;border:1px solid var(--border)}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  thead tr{{background:var(--bg)}}
  thead th{{padding:10px 14px;text-align:left;font-weight:500;font-size:11.5px;color:var(--muted);letter-spacing:.05em;border-bottom:1px solid var(--border);white-space:nowrap}}
  tbody tr{{border-bottom:1px solid var(--border);transition:background .12s}}
  tbody tr:last-child{{border-bottom:none}}
  tbody tr:hover{{background:#f5f0eb}}
  td{{padding:11px 14px;vertical-align:middle}}
  .tag{{display:inline-block;font-size:10.5px;padding:2px 8px;border-radius:3px;font-weight:500;white-space:nowrap}}
  .name{{font-family:'Noto Serif TC',serif;font-size:14px;font-weight:600;line-height:1.4}}
  .loc,.date-cell,.price{{color:var(--muted);font-size:12px;white-space:nowrap}}
  .free{{color:#059669;font-weight:500}}
  .footer{{text-align:center;padding:32px 20px;font-size:11.5px;color:var(--muted);border-top:1px solid var(--border)}}
  @media(max-width:640px){{.loc,.date-cell{{display:none}}td{{padding:10px}}th:nth-child(3),th:nth-child(4){{display:none}}}}
</style>
</head>
<body>
<div class="hero">
  <h1>台北・新北 藝文活動</h1>
  <p class="sub">TAIPEI &amp; NEW TAIPEI ARTS EVENTS</p>
  <div class="badge">{date_range}</div>
  <span class="updated">自動更新於 {generated_at} · {price_note}</span>
</div>
<nav class="nav" id="nav"></nav>
<div class="wrap" id="wrap"></div>
<div class="footer">
  <p>資料由 Gemini AI 搜尋整理 · 活動資訊僅供參考，請以主辦單位公告為準</p>
</div>
<script>
const DATA = {data_json};
const TAGS = {{
  flower:     {{label:'🌸 賞花',   style:'background:#fce4ec;color:#c2185b;border:1px solid #f48fb160'}},
  exhibition: {{label:'🖼️ 展覽',  style:'background:#ede7f6;color:#6a1b9a;border:1px solid #ce93d860'}},
  workshop:   {{label:'🎨 工作坊', style:'background:#e0f7fa;color:#00838f;border:1px solid #80deea60'}},
  performance:{{label:'🎭 表演',   style:'background:#fff8e1;color:#e65100;border:1px solid #ffcc0260'}},
  market:     {{label:'🛍️ 市集',  style:'background:#e8f5e9;color:#2e7d32;border:1px solid #a5d6a760'}},
  music:      {{label:'🎵 音樂',   style:'background:#ffebee;color:#b71c1c;border:1px solid #ef9a9a60'}},
}};
function row(cat, e, showTag) {{
  const tag = showTag ? `<td><span class="tag" style="${{TAGS[cat].style}}">${{TAGS[cat].label}}</span></td>` : '';
  const fc = e.price && (e.price.includes('免費') || e.price === '0') ? 'free' : '';
  return `<tr>${{tag}}<td class="name">${{e.name}}</td><td class="date-cell">${{e.date}}</td><td class="loc">${{e.location}}</td><td class="price ${{fc}}">${{e.price}}</td></tr>`;
}}
function buildSection(id, title, cat, events, showTag) {{
  const rows = events.map(e => row(cat, e, showTag)).join('');
  return `<div class="sec" id="s-${{id}}"><div class="sec-head"><h2 class="sec-title">${{title}}</h2><span class="cnt">${{events.length}} 項</span></div><table><thead><tr>${{showTag?'<th>類別</th>':''}}<th>活動名稱</th><th>日期</th><th>地點</th><th>費用</th></tr></thead><tbody>${{rows}}</tbody></table></div>`;
}}
const nav = document.getElementById('nav');
const wrap = document.getElementById('wrap');
const allEvents = [];
DATA.categories.forEach(cat => {{ allEvents.push(...cat.events.map(e => ({{...e, _cat: cat.key}}))); }});
nav.innerHTML = `<button class="tab on" onclick="show('all',this)">全部 (${{allEvents.length}})</button>`;
wrap.innerHTML = buildSection('all', '✨ 全部活動', null, allEvents, true);
document.querySelector('#s-all table thead tr').innerHTML = '<th>類別</th><th>活動名稱</th><th>日期</th><th>地點</th><th>費用</th>';
document.querySelectorAll('#s-all tbody tr').forEach((tr, i) => {{
  const cat = allEvents[i]._cat;
  tr.querySelector('td').innerHTML = `<span class="tag" style="${{TAGS[cat].style}}">${{TAGS[cat].label}}</span>`;
}});
DATA.categories.forEach(cat => {{
  if (!cat.events.length) return;
  const label = TAGS[cat.key].label;
  nav.innerHTML += `<button class="tab" onclick="show('${{cat.key}}',this)">${{label}} (${{cat.events.length}})</button>`;
  wrap.innerHTML += buildSection(cat.key, label, cat.key, cat.events, false);
}});
document.querySelector('#s-all').classList.add('on');
function show(key, btn) {{
  document.querySelectorAll('.sec').forEach(s=>s.classList.remove('on'));
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('on'));
  document.getElementById('s-'+key).classList.add('on');
  btn.classList.add('on');
}}
</script>
</body>
</html>"""


# ── Gemini API ─────────────────────────────────────
def gemini_search(api_key: str, prompt: str) -> str:
    """呼叫 Gemini API（含 Google Search grounding，讓結果更準確）"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],   # 開啟 Google Search，確保資料是最新的
        "generationConfig": {"temperature": 0.2}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ── 主邏輯 ─────────────────────────────────────────
def get_dates():
    now = datetime.now(TZ)
    end = now + timedelta(days=14)
    return (
        f"{now.strftime('%Y/%m/%d')} – {end.strftime('%Y/%m/%d')}",
        now.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d'),
        now.strftime('%Y/%m/%d %H:%M'),
    )


def fetch_events(api_key: str, cat: dict, start: str, end: str) -> list:
    keywords = CATEGORY_KEYWORDS.get(cat["key"], cat["label"])
    prompt = f"""請搜尋 {start} 到 {end} 這段期間，{CITY_FILTER} 舉辦的「{keywords}」相關活動。

條件：
- 只列台北市或新北市的活動
- 費用超過 NT${MAX_PRICE} 的活動請排除
- 找 5–8 個真實活動

請只回傳 JSON，不要任何說明文字或 markdown，格式：
{{
  "events": [
    {{
      "name": "活動名稱",
      "date": "日期（如 2026/03/20 或 03/20–04/06）",
      "location": "城市・場所名稱",
      "price": "費用（如：免費 / NT$300 / NT$200–500）"
    }}
  ]
}}"""

    try:
        text = gemini_search(api_key, prompt)
        # 移除 markdown code block（如果有的話）
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start_i = text.find("{")
        end_i = text.rfind("}") + 1
        if start_i >= 0:
            return json.loads(text[start_i:end_i]).get("events", [])
    except Exception as e:
        print(f"  ⚠ {cat['label']}: {e}")
    return []


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ 請設定環境變數 GEMINI_API_KEY")
        raise SystemExit(1)

    print("🎨 台北・新北 藝文活動收集器（Gemini 版）")
    date_range, start, end, generated_at = get_dates()
    print(f"📅 {date_range}\n")

    all_data = []
    for cat in CATEGORIES:
        print(f"搜尋 {cat['label']} ...", end=" ", flush=True)
        events = fetch_events(api_key, cat, start, end)
        all_data.append((cat, events))
        print(f"找到 {len(events)} 項")

    total = sum(len(e) for _, e in all_data)
    print(f"\n✅ 共 {total} 項活動")

    payload = {"categories": [{"key": c["key"], "events": ev} for c, ev in all_data]}
    html = HTML.format(
        date_range=date_range,
        generated_at=generated_at,
        price_note=PRICE_NOTE,
        data_json=json.dumps(payload, ensure_ascii=False),
    )
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("📄 已產出 index.html")


if __name__ == "__main__":
    main()
