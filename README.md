# 台北・新北 藝文活動

每週日晚上 21:00 自動更新，收集未來兩週台北・新北的藝文活動。

🔗 **活動頁面：** `https://你的帳號.github.io/arts-events/`

---

## 活動類別
🌸 賞花 ・ 🖼️ 展覽 ・ 🎨 工作坊 ・ 🎭 表演 ・ 🛍️ 市集 ・ 🎵 音樂演出

費用超過 NT$1,000 的活動不列入。

---

## 設定方式

### 1. Fork 這個 Repo

### 2. 設定 API Key
進入 Repo → **Settings → Secrets and variables → Actions**
→ 點「New repository secret」
→ Name: `ANTHROPIC_API_KEY`，Value: 貼上你的 API Key

### 3. 開啟 GitHub Pages
進入 Repo → **Settings → Pages**
→ Source 選 **「GitHub Actions」**

### 4. 手動執行一次確認
進入 **Actions → 每週自動更新藝文活動 → Run workflow**

執行完後，網址 `https://你的帳號.github.io/arts-events/` 就會上線。

---

## 修改設定

編輯 `collector.py` 開頭的設定區塊：

```python
CITY_FILTER = "台北市、新北市"   # 要收集的城市
MAX_PRICE   = 1000               # 費用上限（NT$）
```
