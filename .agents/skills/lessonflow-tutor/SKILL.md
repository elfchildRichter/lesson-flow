---
name: lessonflow-tutor
description: Lesson Flow 教務小老師 Skill。負責處理教材解析、問答流調優、簡報大綱與逐頁演講稿生成、Self-RAG 幻覺審查與 LaTeX 數學公式格式處理。
---

# Lesson Flow 教務教學部 (教務小老師)

## 部門定位與核心職責
教務教學部是 Lesson Flow 的資深教學內容專家，負責維護 AI 助教的學術嚴謹度、簡報品質與回答親和力。

### 主要任務：
1. **教材解析 (Multimodal Vision RAG)**：高畫質 PNG 頁面與 VLM 結合解析，精準擷取圖表、表格與內容。
2. **問答工作流 (QA Flow)**：維護 [`app/workflows/qa_graph.py`](file:///Users/Archer/Repos/lesson_flow/app/workflows/qa_graph.py)，包含檢索相關性審查 (grade_documents)、Self-RAG 防幻覺驗證 (check_hallucination) 與網路搜尋降級。
3. **教學簡報與演講稿生成 (Deck Flow)**：維護 [`app/workflows/deck_graph.py`](file:///Users/Archer/Repos/lesson_flow/app/workflows/deck_graph.py)，產出高品質 `.pptx` 結構與逐頁教學演講稿 `.md`。
4. **數學公式與格式排版**：確保所有產出的 LaTeX 公式精準使用 `$...$` (行內) 或 `$$...$$` (區塊) 格式。

---

## 🛠️ 相關檔案與核心組件
- [`app/workflows/qa_graph.py`](file:///Users/Archer/Repos/lesson_flow/app/workflows/qa_graph.py)：問答狀態圖與 Self-RAG
- [`app/workflows/deck_graph.py`](file:///Users/Archer/Repos/lesson_flow/app/workflows/deck_graph.py)：簡報與講稿 StateGraph
- [`app/services.py`](file:///Users/Archer/Repos/lesson_flow/app/services.py)：RAG 檢索與 LLM 答案生成函數

---

## 📋 標準作業規範 (SOP)

### 1. 修改 Prompt 或 Schema 時的規範
- **出處標示**：所有 QA 回答必須包含精準頁碼標籤（如 `[P.3]`）。
- **OpenAI Strict Mode 防護**：修改 JSON Schema 時，所有 `type: "object"` 層級**必須包含 `"additionalProperties": false`**，防止 API 傳回 400 Bad Request。
- **多語言支援 (zh-TW / en)**：生成答案或講稿時，遵循使用者指定的 `language` 參數。

### 2. 演講稿與簡報產出品質要求
- 每張 Slide 必須對應獨立的講稿段落。
- 講稿語氣需適合教師授課或學生自學，包含口語化過渡句與重點強調。
