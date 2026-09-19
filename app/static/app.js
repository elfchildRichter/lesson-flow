const state = {
  document: null,
  deck: null,
  activeSlide: 0,
  user: null,
  provider: null,
  activeDept: null,
  agentHistory: [],
  lang: localStorage.getItem('app_lang') || 'zh-TW'
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const translations = {
  'zh-TW': {
    'nav.brand': '課伴<small>LESSONFLOW (Alpha)</small>',
    'nav.brand_root': '課伴',
    'nav.home': '產品介紹',
    'nav.workspace': '工作台',
    'nav.deck': '產出預覽',
    'nav.chat': '教材問答',
    'nav.profile': '個人帳號設定',
    'nav.admin': '管理員控制台',
    'nav.agent': 'AI 備課助手',
    'nav.crumb_home': '產品介紹',
    'nav.crumb_create': '教學設計工作台',
    'nav.crumb_workspace': '教學設計工作台',
    'nav.crumb_deck': '教學產出預覽',
    'nav.crumb_chat': '教材問答知識庫',
    'nav.crumb_admin': '管理員控制台',
    'nav.crumb_agent': 'AI 備課助手',
    'nav.crumb_profile': '個人帳號設定',
    'nav.sub_home': '把教材變成一堂好懂的課',
    'nav.sub_workspace': '上傳教材、解析內容與一鍵生成教學資產',
    'nav.sub_deck': '檢視、編輯與匯出簡報、講義與測驗題庫',
    'nav.sub_chat': '依據教材精準溯源與概念解說',
    'nav.sub_agent': '教案設計、試題與教學宣傳多功能助手',
    'nav.sub_profile': '檢視帳號身份、等級與每日配額',
    'nav.sub_admin': '審核帳號、調整權限與用戶管理',
    'chat.btn_clear': '開啟新對話',
    'chat.memory_active': '多輪對話記憶中',
    'agent.btn_clear': '清空對話',
    'preview.eyebrow': '課程產出與預覽',
    'preview.title': '教學產出預覽',
    'preview.subtitle': '在此檢視並匯出已生成的教學簡報、隨堂講義與單元試卷。',
    'preview.tab_deck': '教學簡報與講稿',
    'preview.tab_handout': 'A4 隨堂講義',
    'preview.tab_quiz': '單元試卷評量',
    'agent.eyebrow': '💡 AI 教師備課與任務助手',
    'agent.title': '💡 AI 備課助手',
    'agent.subtitle': '自動為您設計單元教案大綱、生成測驗題庫、撰寫講稿大綱與 FB/Threads 社群教學宣傳貼文。',
    'agent.toggle_collapse': '收合部門卡片',
    'agent.toggle_expand': '展開卡片',
    'agent.current_dept_tag': '🏢 當前諮詢',
    'agent.metric_depts': '4 大專家助手',
    'agent.metric_depts_sub': '教務備課 · 題庫生成 · 行銷推廣 · 限額查詢',
    'agent.metric_skills': '5 個 Skills',
    'agent.metric_skills_sub': '外掛式動態註冊表 (Registry)',
    'agent.metric_router': 'CompanyRouter',
    'agent.metric_router_sub': '意圖自適應分流與容錯',
    'agent.dept_status_active': '🟢 服務中',
    'agent.dept_academic_title': '教務教學部',
    'agent.dept_academic_role': '教務小老師',
    'agent.dept_academic_desc': '負責教材解析、問答流調優、單元教案大綱、試題與簡報逐頁演講稿生成。',
    'agent.dept_ops_title': '營運與行政部',
    'agent.dept_ops_role': '教務行政特助',
    'agent.dept_ops_desc': '負責學校/機構團體合約、席位授權撥發、帳號開通與團隊權限維護。',
    'agent.dept_mkt_title': '市場與營銷部',
    'agent.dept_mkt_role': '營銷推廣專員',
    'agent.dept_mkt_desc': '負責課程宣傳推廣、教學賣點包裝、招生文案與 FB/Threads/LinkedIn 社群貼文生成。',
    'agent.dept_devops_title': '技術維護部',
    'agent.dept_devops_role': '技術維護工程師',
    'agent.dept_devops_desc': '負責 JWT 身份驗證排查、系統 Quota 限額控管、Railway 部署與 OOM 診斷。',
    'agent.dept_mkt_platform_label': '文案推廣平台：',
    'agent.welcome_title': '💡 歡迎使用 AI 備課助手',
    'agent.welcome_desc': '請下達備課或教學任務（例如：「設計牛頓運動定律 45 分鐘教案」、「出 5 題高中生物題」或「寫一篇教學心得」）。',
    'agent.sug_1': '🎓 45 分鐘教案設計',
    'agent.sug_2': '📝 5 題生物選擇題與解析',
    'agent.sug_3': '🚀 FB/Threads 社群推廣文案',
    'agent.sug_4': '📋 查詢會員等級與每日配額',
    'agent.placeholder': '下達備課或教學任務 (例: \'幫我設計一份 45 分鐘物理教案大綱\' 或 \'出 5 題選擇題\')...',
    'agent.shortcut': '<span>↵</span> Enter 傳送 · Shift + Enter 換行',
    'provider.title': '⚡ AI 模型提供者',
    'multimodal.title': '📷 教材解析設定',
    'multimodal.toggle_label': '圖表與理化公式辨識',
    'multimodal.hint': '開啟使用圖表與公式解析（消耗 30 點，標準解析為 5 點）',
    'quota.title': '每日備課點數',
    'quota.daily_remaining': '今日剩餘點數',
    'quota.hint_main': '簡報 50 · 講義 30 · 試卷 20 · 微調 3 點',
    'quota.unlogged': '未登入',
    'quota.unlimited': '👑 無限配額',
    'quota.active': '已開通',
    'quota.admin': '👑 管理員',
    'quota.deck_label': '教學簡報',
    'quota.handout_label': '隨堂講義',
    'quota.quiz_label': '單元試卷',
    'quota.ask_label': '文件提問',
    'quota.upload_label': '教材上傳',
    'quota.guest': '訪客用戶',
    'quota.login_hint': '點擊登入帳號',
    'deck.btn_print_handout': '🖨️ A4 講義列印',
    'deck.btn_deck_to_quiz': '🎯 依簡報出題',
    'topbar.status_ready': '系統就緒',
    'topbar.login_reg': '登入 / 註冊',
    'topbar.logout': '登出',

    'hero.eyebrow': 'AI 教學設計工作台',
    'workspace.title': 'AI 教學設計工作台',
    'workspace.subtitle': '可直接上傳教材或與 AI 備課助手討論構思，完整產出好教好懂的講義、簡報與試卷；支援知識補充檢索、隨時手動修訂，讓備課與上課更順暢。',
    'hero.title': '把教材，變成一堂<br><em>真正好懂的課。</em>',
    'hero.title_em': '真正好懂的課。',
    'hero.subtitle': '可直接上傳教材或與 AI 備課助手討論構思，完整產出好教好懂的講義、簡報與試卷；支援知識補充檢索、隨時手動修訂，讓備課與上課更順暢。',
    'hero.copy': '可直接上傳教材或與 AI 備課助手討論構思，完整產出好教好懂的講義、簡報與試卷，<br>支援知識補充檢索、隨時手動修訂，讓備課與上課更順暢。',
    'hero.toggle_collapse': '收合介紹',
    'hero.toggle_expand': '展開介紹',
    'hero.collapsed_title': '把教材，變成一堂真正好懂的課。',
    'auth_brand.eyebrow': '✦ 課伴 LessonFlow',
    'auth_brand.title': '把教材，變成一堂<br><em>真正好懂的課。</em>',
    'auth_brand.copy': '可直接上傳教材或與 AI 備課助手討論構思，完整產出好教好懂的講義、簡報與試卷；支援知識補充檢索、隨時手動修訂，讓備課與上課更順暢。',
    'steps.step1_title': '輸入或構思',
    'steps.step1_sub': 'PDF 解析 · AI 討論',
    'steps.step2_title': '設定目標',
    'steps.step2_sub': '對象、語氣與節奏',
    'steps.step3_title': '完整產出',
    'steps.step3_sub': '講義 · 簡報 · 試卷',
    'home.btn_start': '🚀 進入工作台開始備課',
    'home.btn_agent': '💡 諮詢 AI 備課助手',
    'home.feat1_title': '多模態與標準教材解析',
    'home.feat1_desc': '常規教材採「標準文字解析」即可達到高水準教學設計，高速省額度；含理化公式或幾何圖表之教材，可啟用「多模態深度解析」精準理解圖像。',
    'home.feat4_title': '教材問答與精準溯源',
    'home.feat4_desc': '專屬教材助教，預設嚴格根據上傳教材之原文段落回答並附上精準頁碼，確保教學依據真實可考、絕不憑空捏造；亦可按需啟用聯網搜尋，補充外部延伸知識與時事案例。',
    'home.feat3_title': '隨堂講義與試卷評量',
    'home.feat3_desc': '一鍵生成 A4 導讀手冊與具備誘答解析的單元測驗卷，支援學生測驗卷與教師詳解模式，提供 Word / PDF 高清匯出。',
    'home.feat2_title': '教學簡報與逐頁講稿',
    'home.feat2_desc': '循序漸進投影片架構，每頁配備核心圖解提示與教師專屬逐頁演講稿，支援線上就地手動微調並同步匯出 PPTX / Word。',
    'home.feat5_title': 'AI 專家備課助手 (4 大部門與智慧導航)',
    'home.feat5_desc': '手邊無現成教材也能備課！內建「教務教學部、營運行政部、市場營銷部、技術維護部」4 大專家部門，可針對特定任務深度諮詢；亦可直接使用「全域智慧導航模式」，系統自動精準分派至對應專業助手，構思教案後可一鍵銜接全套產出。',
    'upload.title': '選擇你的教材',
    'upload.secure': '✓ 安全加密',
    'upload.drag': '拖曳 PDF 到這裡',
    'upload.click': '或點擊選擇電腦中的檔案',
    'upload.limit': '最大 30 MB · 支援可選取文字的 PDF',
    'upload.sample_hint': '💡 手邊暫無教材？可與 AI 備課助手討論主題，直接生成完整教案：',
    'upload.agent_btn': '💡 前往 AI 備課助手討論',
    'upload.sample_btn': '🚀 載入示範教材 (高中物理)',
    'upload.parsed_ready': '教材已建立索引，可開始教學設計',
    'preview.editable_hint': '<b>✎ 就地手動編修</b>：點擊下方任何標題、講稿、條列或題目文字均可直接免費修改，系統將自動同步並套用於匯出檔案。',
    'settings.title': '教學設計工作台',
    'settings.status_wait': '等待教材',
    'settings.audience': '學習對象',
    'settings.tone': '教學語氣',
    'settings.duration': '課程時間',
    'settings.slide_count': '簡報頁數',
    'settings.language': '輸出語言',
    'settings.web_search': '開啟網路補充搜尋（延伸案例數據）',
    'settings.generate_btn': '生成教學內容',
    'settings.estimate': '預計需要 1–2 分鐘，可留在此頁等待',
    'value.01_title': '實證為本',
    'value.01_desc': '以教材核心為基準，支援精準頁碼溯源與聯網補充',
    'value.02_title': '教學設計',
    'value.02_desc': '循序漸進架構，每頁皆有明確教學目標與講稿',
    'value.03_title': '即刻匯出',
    'value.03_desc': '一鍵匯出 PPTX 簡報、Word 講義與測驗試卷',

    'workspace.common_title': '✦ 共通教學設定 (通用於下方三大產出模組)',
    'workspace.generate_all': '🚀 一鍵生成全套教案 (講義+簡報+試卷)',
    'handout.badge': '📝 模組 1',
    'handout.title': '隨堂講義',
    'handout.desc': 'A4 導讀手冊、核心觀念與研讀建議',
    'handout.audience': '適用對象',
    'handout.detail': '詳細程度',
    'handout.web_search': '開啟網路知識補充（整合時事案例）',
    'handout.btn_to_workbench': '🎯 參考講義調整教學設計',
    'handout.btn_print': '🖨️ A4 預覽列印 (另存 PDF)',
    'handout.btn_download_docx': '📄 下載 Word (.docx)',
    'handout.btn': '📝 生成 A4 隨堂講義',
    'deck.badge': '🎯 模組 2',
    'deck.title': '教學簡報',
    'deck.desc': '投影片大綱、視覺圖解與逐頁講稿',
    'deck.web_search': '開啟網路補充搜尋（延伸案例數據）',
    'deck.btn': '✦ 生成教學簡報',
    'deck.btn_pdf': '📑 下載簡報 (PDF)',
    'deck.btn_pptx': '📊 下載簡報 (.pptx)',
    'deck.btn_print_handout': '🖨️ 講稿列印 (另存 PDF)',
    'deck.btn_docx': '📄 下載講稿 (.docx)',
    'deck.btn_download_docx': '📄 下載講稿 (.docx)',
    'quiz.badge': '📑 模組 3',
    'quiz.title': '單元試卷',
    'quiz.desc': '隨堂測驗評量、誘答選項與觀念詳解',
    'quiz.count': '出題題數',
    'quiz.difficulty': '試題難度',
    'quiz.web_search': '開啟外部題庫檢索（搜尋真實考題）',
    'quiz.btn': '📑 生成單元試卷',
    'quiz.teacher_mode_toggle': '✔ 顯示解答與詳細解析 (教師版)',
    'quiz.btn_print': '🖨️ 列印考卷 (另存 PDF)',
    'quiz.btn_download_docx': '📄 下載考卷 (.docx)',

    'opt.audience.college': '大學生',
    'opt.audience.high': '高中生',
    'opt.audience.middle': '國中生',
    'opt.audience.elementary': '國小生',
    'opt.audience.adult': '職場成人',
    'opt.audience.general': '一般大眾',
    'opt.tone.clear': '清楚易懂',
    'opt.tone.lively': '活潑互動',
    'opt.tone.rigorous': '專業嚴謹',
    'opt.tone.story': '故事引導',

    'opt.handout_aud.student': '學生/學習者',
    'opt.handout_aud.instructor': '授課講師備課用',
    'opt.handout_aud.pro': '職場專業培訓學員',
    'opt.handout_aud.self': '自學者筆記',

    'opt.handout_det.concise': '重點摘要型 (精簡)',
    'opt.handout_det.standard': '標準導讀型 (平衡)',
    'opt.handout_det.detailed': '深入剖析型 (詳盡)',

    'opt.quiz_cnt.3': '3 題 (課堂速測)',
    'opt.quiz_cnt.5': '5 題 (標準小考)',
    'opt.quiz_cnt.8': '8 題 (單元測驗)',
    'opt.quiz_cnt.10': '10 題 (總結評量)',

    'opt.quiz_diff.all': '混合難度 (循序漸進)',
    'opt.quiz_diff.easy': '基礎概念題',
    'opt.quiz_diff.medium': '中等理解題',
    'opt.quiz_diff.hard': '進階論述與計算題',

    'opt.provider.gemini': 'Gemini 雲端 (Cloud API) ✨',
    'opt.provider.ollama_cloud': 'Ollama 雲端 (Cloud API)',
    'opt.provider.ollama_local': 'Ollama 本機 (Local LLM)',
    'opt.provider.openai': 'OpenAI 雲端 (GPT-4o)',

    'opt.duration.20': '20 分鐘',
    'opt.duration.30': '30 分鐘',
    'opt.duration.45': '45 分鐘',
    'opt.duration.60': '60 分鐘',
    'opt.duration.90': '90 分鐘',

    'opt.slides.6': '6 頁',
    'opt.slides.8': '8 頁',
    'opt.slides.10': '10 頁',
    'opt.slides.12': '12 頁',
    'opt.slides.15': '15 頁',

    'opt.lang.zh_tw': '🇹🇼 中文 (Traditional Chinese)',
    'opt.lang.en': '🇺🇸 English',
    'opt.lang.auto': '🤖 與教材同語系 (Auto)',

    'deck.eyebrow': '教學內容已就緒',
    'deck.title': '教學簡報',
    'deck.subtitle': '上傳教材後開始生成。',
    'deck.btn_pdf': '📑 下載簡報 (PDF)',
    'deck.btn_script': '🖨️ 講稿列印 (另存 PDF)',
    'deck.btn_pptx': '📊 下載簡報 (.pptx)',
    'deck.empty_slide': '還沒有簡報',
    'deck.stage_empty_b': '尚未產生內容',
    'deck.stage_empty_s': '回到工作台上傳教材並設定課程',
    'deck.preview_empty_b': '尚未生成教學簡報',
    'deck.preview_empty_s': '請在工作台點擊「✦ 生成教學簡報」或「🚀 一鍵生成全套教案」',
    'deck.preview_empty_btn': '← 前往工作台生成',
    'deck.notes_label': '這頁怎麼說',
    'deck.page_ref': '講者備註',
    'deck.speaker_notes_placeholder': '生成後，逐頁講稿會顯示在這裡。',

    'chat.eyebrow': '文件知識庫',
    'chat.title': '問教材，不問網路。',
    'chat.subtitle': '每個回答都以你的文件為依據，並附上可核對的來源頁碼。',
    'chat.doc_empty_b': '尚未選擇教材',
    'chat.doc_empty_s': '請先回到工作台上傳',
    'chat.welcome_b': '嗨，我是你的教材助教',
    'chat.welcome_p': '上傳文件後，你可以請我解釋概念、比較差異，或從教材中整理重點。我只會根據文件內容回答。',
    'chat.sug_1': '這份教材的三個核心重點是什麼？',
    'chat.sug_2': '用簡單的例子解釋最重要的概念',
    'chat.web_search': '開啟網路補充搜尋（教材中查無解答時聯網檢索）',
    'chat.placeholder': '向教材提問…',
    'chat.shortcut': '<span>↵</span> Enter 傳送 · Shift + Enter 換行',

    'admin.eyebrow': '系統權限與用戶審核',
    'admin.title': '👑 管理員控制台',
    'admin.subtitle': '審核新註冊帳號、調整權限、重置密碼與維護全系統使用者。',
    'admin.btn_create_user': '➕ 新增用戶 / 管理員',
    'admin.metric_total': '系統總帳號數',
    'admin.metric_pending': '待開通審核',
    'admin.metric_admin': '系統管理員',
    'admin.th_id': 'ID',
    'admin.th_username': '帳號名稱',
    'admin.th_tier': '會員層級 / 角色',
    'admin.th_daily_usage': '今日使用 / 限額',
    'admin.th_total_usage': '累計總使用量',
    'admin.th_last_login': '上次上線時間',
    'admin.th_role': '角色',
    'admin.th_status': '審核狀態',
    'admin.th_created': '建立時間',
    'admin.th_actions': '管理操作',
    'admin.loading': '載入中…',
    'admin.create_modal_title': '➕ 新增帳號 (管理員開通)',
    'admin.create_modal_sub': '直接為系統建立已開通權限之一般用戶或管理員帳號',
    'admin.create_lbl_username': '帳號名稱 (Username)',
    'admin.create_lbl_password': '初始密碼 (Password)',
    'admin.create_lbl_role': '身分角色 (Role)',
    'admin.create_lbl_tier': '會員層級 (Tier)',
    'admin.create_btn_submit': '確認建立帳號',
    'admin.opt_role_user': '👤 一般用戶 (user)',
    'admin.opt_role_admin': '👑 系統管理員 (admin)',
    'admin.opt_tier_trial': '🎓 教師試用版 (100 點/日)',
    'admin.opt_tier_pro': '⭐ 教師專業版 (1,000 點/日)',
    'admin.opt_tier_inst': '🏫 機構/學校版 (10,000 點/日)',

    'profile.eyebrow': '個人帳號與安全性設定',
    'profile.title': '⚙️ 個人帳號設定',
    'profile.subtitle': '檢視您的帳號身分、每日配額使用狀況並進行密碼修改。',
    'profile.basic_title': '帳號基本資訊',
    'profile.role_user': '一般用戶',
    'profile.role_admin': '系統管理員',
    'profile.lbl_username': '帳號名稱',
    'profile.lbl_role': '帳號權限',
    'profile.lbl_quota': '每日提問配額',
    'profile.btn_logout': '登出系統',
    'profile.change_pass_title': '修改個人密碼',
    'profile.lbl_old_pass': '原密碼',
    'profile.lbl_new_pass': '新密碼',
    'profile.ph_old_pass': '輸入原密碼',
    'profile.ph_new_pass': '輸入新密碼 (至少4字元)',
    'profile.btn_save_pass': '儲存新密碼',

    'auth.tab_login': '用戶登入',
    'auth.tab_register': '註冊新帳號',
    'auth.login_title': '歡迎回來',
    'auth.login_sub': '請輸入您的帳號與密碼以取得 API 使用權限與配額',
    'auth.lbl_username': '帳號',
    'auth.lbl_password': '密碼',
    'auth.ph_username': '輸入帳號',
    'auth.ph_password': '輸入密碼',
    'auth.btn_login': '登入系統',
    'auth.reg_title': '建立新帳號',
    'auth.reg_sub': '註冊後需經管理員開通，方可登入並開始使用每日 20 次提問額度',
    'auth.ph_reg_user': '長度至少 3 個字元',
    'auth.ph_reg_pass': '長度至少 4 個字元',
    'auth.btn_register': '送出註冊',

    'loading.read_title': '正在讀懂你的教材',
    'loading.read_copy': '整理章節與核心概念…',
    'loading.read_multimodal_copy': '正在辨識圖表、表格與理化公式，處理時間稍長請稍候…',
    'loading.read_fast_copy': '正在快速讀取純文字內容與章節結構…',
    'loading.deck_title': '正在規劃教學架構與講稿…',
    'loading.deck_copy': '運用 LLM 設計教學流程與產生簡報，約需時數分鐘…',
    'loading.ask_title': '正在對照教材內容並生成最佳解答…',
    'loading.ask_copy': '從章節段落精準索引並附上頁碼說明…',
    'stepper.step1_title': '上傳 / 構思教材',
    'stepper.step1_sub': 'PDF / AI 助手',
    'stepper.step2_title': '設定對象與語氣',
    'stepper.step2_sub': '共通教學參數',
    'stepper.step3_title': '生成隨堂講義',
    'stepper.step3_sub': '確立核心知識母本',
    'stepper.step4_title': '衍生簡報與試卷',
    'stepper.step4_sub': '簡報與試卷',
    'workspace.generate_all': '🚀 循序生成全套（講義 ➔ 簡報 & 試卷）',
    'handout.badge': '📝 模組 1',
    'deck.badge': '🎯 模組 2',
    'quiz.badge': '📑 模組 3',
    'profile.top_badge': '帳號管理中心',
    'profile.btn_refresh': '重新整理',
    'toast.profile_refreshed': '帳號資訊已更新',

    'footer.copyright': '© 2026 ArchCet. All rights reserved.',
    'footer.terms': '服務條款 (Terms)',
    'footer.privacy': '隱私權政策 (Privacy)',
    'footer.contact': '聯絡我們'
  },
  'en': {
    'nav.brand': 'LessonFlow<small>(Alpha)</small>',
    'nav.brand_root': 'LessonFlow',
    'nav.home': 'Product Overview',
    'nav.workspace': 'Workspace',
    'nav.deck': 'Outputs & Review',
    'nav.chat': 'Material Q&A',
    'nav.profile': 'Account Settings',
    'nav.admin': 'Admin Console',
    'nav.agent': 'AI Lesson Assistant',
    'nav.crumb_home': 'Product Overview',
    'nav.crumb_create': 'Instructional Workspace',
    'nav.crumb_workspace': 'Instructional Workspace',
    'nav.crumb_deck': 'Outputs & Review',
    'nav.crumb_chat': 'Material Q&A',
    'nav.crumb_admin': 'Admin Console',
    'nav.crumb_agent': 'AI Lesson Assistant',
    'nav.crumb_profile': 'Account Settings',
    'nav.sub_home': 'Turn Teaching Materials into Engaging Lessons',
    'nav.sub_workspace': 'Upload Materials & Generate Teaching Assets',
    'nav.sub_deck': 'Preview & Export Slides, Handouts and Quizzes',
    'nav.sub_chat': 'Grounded Q&A & Concept Explanations',
    'nav.sub_agent': 'Multi-department Lesson Prep & Teaching Assistant',
    'nav.sub_profile': 'Manage Account, Tier & Quotas',
    'nav.sub_admin': 'User Management & Permissions',
    'chat.btn_clear': 'New Session',
    'chat.memory_active': 'Multi-turn Memory Active',
    'agent.btn_clear': 'Reset Chat',
    'preview.eyebrow': 'Course Outputs & Preview',
    'preview.title': 'Outputs & Preview Center',
    'preview.subtitle': 'Inspect and export generated presentation decks, A4 handouts, and unit quiz sheets.',
    'preview.tab_deck': 'Slides & Speaker Notes',
    'preview.tab_handout': 'A4 Handout',
    'preview.tab_quiz': 'Unit Quiz Sheet',
    'preview.editable_hint': '<b>✎ Live Inline Editing</b>: Click on any slide title, notes, bullets, or quiz questions below to edit directly for free. Changes will sync to exported files automatically.',
    'agent.eyebrow': '💡 AI Lesson Preparation & Task Assistant',
    'agent.title': '💡 AI Lesson Assistant',
    'agent.subtitle': 'Automatically design lesson plan outlines, generate quiz questions with explanations, and draft social teaching posts.',
    'agent.toggle_collapse': 'Collapse Cards',
    'agent.toggle_expand': 'Expand Cards',
    'agent.current_dept_tag': '🏢 Department',
    'agent.metric_depts': '4 AI Assistants',
    'agent.metric_depts_sub': 'Lesson Plan · Quiz Generator · Social Post · Quota Checker',
    'agent.metric_skills': '5 Skills',
    'agent.metric_skills_sub': 'Extensible Skill Registry',
    'agent.metric_router': 'CompanyRouter',
    'agent.metric_router_sub': 'Adaptive Intent Routing & Fallback',
    'agent.dept_status_active': '🟢 Active',
    'agent.dept_academic_title': 'Academic & Teaching',
    'agent.dept_academic_role': 'LessonFlow Tutor',
    'agent.dept_academic_desc': 'Handles material parsing, Q&A, lesson plan outlines, quiz questions, and slide deck scripts.',
    'agent.dept_ops_title': 'Operations & Admin',
    'agent.dept_ops_role': 'Operations Assistant',
    'agent.dept_ops_desc': 'Handles school/institution licensing, member seat allocation, account approvals, and org permissions.',
    'agent.dept_mkt_title': 'Marketing & Sales',
    'agent.dept_mkt_role': 'Marketing Specialist',
    'agent.dept_mkt_desc': 'Promotes your courses, packages teaching highlights, creates enrollment copy, and generates social media posts.',
    'agent.dept_devops_title': 'DevOps & Maintenance',
    'agent.dept_devops_role': 'DevOps Engineer',
    'agent.dept_devops_desc': 'Handles JWT auth diagnostics, system quota enforcement, Railway deployments, and OOM analysis.',
    'agent.dept_mkt_platform_label': 'Target Platform:',
    'agent.welcome_title': '💡 Welcome to AI Lesson Assistant',
    'agent.welcome_desc': 'Enter any lesson plan or teaching task (e.g. "Design a 45-min Physics lesson plan", "Generate 5 Biology quiz questions", or "Write a teaching post").',
    'agent.sug_1': '🎓 45-min Lesson Plan Design',
    'agent.sug_2': '📝 5 Biology Quiz Questions',
    'agent.sug_3': '🚀 FB/Threads Promo Post',
    'agent.sug_4': '📋 Check Tier & Daily Quota',
    'agent.placeholder': 'Enter teaching task (e.g. \'Design a 45-min Physics lesson plan\' or \'Generate 5 quiz questions\')...',
    'agent.shortcut': '<span>↵</span> Enter to send · Shift + Enter for new line',
    'provider.title': '⚡ AI Provider',
    'multimodal.title': '📷 PDF Reading Mode',
    'multimodal.toggle_label': 'Formula & Diagram Recognition',
    'multimodal.hint': 'Enable formula & diagram parsing (Costs 30 credits, Standard parsing is 5 credits)',
    'quota.title': 'Daily Credits',
    'quota.daily_remaining': 'Remaining Credits',
    'quota.hint_main': 'Deck 50 · Handout 30 · Quiz 20 · Refine 3 pts',
    'quota.unlogged': 'Not Logged In',
    'quota.unlimited': '👑 Unlimited Quota',
    'quota.active': 'Active',
    'quota.admin': '👑 Admin',
    'quota.regular': 'Regular User',
    'quota.deck_label': 'Decks',
    'quota.handout_label': 'Handouts',
    'quota.quiz_label': 'Quizzes',
    'quota.ask_label': 'Q&A',
    'quota.upload_label': 'Uploads',
    'quota.guest': 'Guest User',
    'quota.login_hint': 'Click to login',
    'deck.btn_print_handout': '🖨️ A4 Handout Print',
    'deck.btn_deck_to_quiz': '🎯 Generate Quiz from Deck',
    'topbar.status_ready': 'System Ready',
    'topbar.login_reg': 'Sign In / Register',
    'topbar.logout': 'Log Out',

    'hero.eyebrow': 'AI Instructional Design Workspace',
    'workspace.title': 'AI Instructional Design Workspace',
    'workspace.subtitle': 'Upload materials or brainstorm with AI teaching assistants to generate engaging handouts, slide decks, and quiz sheets; with knowledge search and live editing to streamline your teaching.',
    'hero.title': 'Transform Materials into<br><em>Truly Engaging Lessons.</em>',
    'hero.title_em': 'Truly Engaging Lessons.',
    'hero.subtitle': 'Upload materials or brainstorm with AI teaching assistants to generate engaging handouts, slide decks, and quiz sheets; with knowledge search and live editing to streamline your teaching.',
    'hero.copy': 'Upload materials or brainstorm with AI teaching assistants to craft structured handouts, slide decks, and quizzes,<br>with knowledge search and instant manual editing.',
    'hero.toggle_collapse': 'Collapse Intro',
    'hero.toggle_expand': 'Expand Intro',
    'hero.collapsed_title': 'Turn materials into clear, structured lessons.',
    'auth_brand.eyebrow': '✦ LessonFlow',
    'auth_brand.title': 'Transform Materials into<br><em>Truly Engaging Lessons.</em>',
    'auth_brand.copy': 'Upload materials or brainstorm with AI teaching assistants to generate engaging handouts, slide decks, and quiz sheets; with knowledge search and live editing to streamline your teaching.',
    'steps.step1_title': 'Input & Ideate',
    'steps.step1_sub': 'PDF · AI Chat',
    'steps.step2_title': 'Set Target',
    'steps.step2_sub': 'Audience & Tone',
    'steps.step3_title': 'Full Output',
    'steps.step3_sub': 'Handout · Deck · Quiz',
    'home.btn_start': '🚀 Launch Instructional Workspace',
    'home.btn_agent': '💡 Consult AI Lesson Assistant',
    'home.feat1_title': 'Standard & Multimodal Parsing',
    'home.feat1_desc': 'Fast Standard OCR delivers high quality for text materials while saving credits; enable Multimodal VLM for deep formula and diagram comprehension.',
    'home.feat4_title': 'Material Q&A & Source Citations',
    'home.feat4_desc': 'Dedicated material copilot that strictly answers based on uploaded documents with exact page citations to prevent hallucinations; optional web search can be toggled for external case studies.',
    'home.feat3_title': 'A4 Handouts & Unit Quizzes',
    'home.feat3_desc': 'Generate study guides and quiz sheets with distractor rationales, student/teacher modes, and Word/PDF export support.',
    'home.feat2_title': 'Slide Decks & Speaker Notes',
    'home.feat2_desc': 'Progressive slide structure with conceptual visual cues and comprehensive speaker notes, editable directly on-screen.',
    'home.feat5_title': 'AI Expert Lesson Assistant (4 Departments & Auto-Routing)',
    'home.feat5_desc': 'No PDF at hand? Brainstorm with 4 specialized expert departments (Academic, Ops, Marketing, DevOps) or use the unified Omni Auto-Router to automatically route tasks and generate full lesson plans directly.',
    'upload.title': 'Select Your Material',
    'upload.secure': '✓ Secure & Encrypted',
    'upload.drag': 'Drag & Drop PDF Here',
    'upload.click': 'or click to browse files',
    'upload.limit': 'Max 30 MB · Selectable text PDF supported',
    'upload.sample_hint': '💡 No material at hand? Chat with AI Assistant to draft a complete lesson plan:',
    'upload.agent_btn': '💡 Consult AI Assistant',
    'upload.sample_btn': '🚀 Load Sample Lesson (Physics)',
    'upload.parsed_ready': 'Material indexed, ready for lesson design',
    'settings.title': 'Instructional Design Workspace',
    'settings.status_wait': 'Awaiting Material',
    'settings.audience': 'Audience',
    'settings.tone': 'Teaching Tone',
    'settings.duration': 'Duration',
    'settings.slide_count': 'Slide Count',
    'settings.language': 'Output Language',
    'settings.web_search': 'Enable Web Search (Supplement cases & data)',
    'settings.generate_btn': 'Generate Lesson Content',
    'settings.estimate': 'Takes about 1–2 minutes, feel free to wait here',
    'value.01_title': 'Evidence-Grounded',
    'value.01_desc': 'Anchored in source materials with page citations & web supplements',
    'value.02_title': 'Instructional Design',
    'value.02_desc': 'Structured learning, not just summaries',
    'value.03_title': 'Instant Export',
    'value.03_desc': 'Download PPTX, Word handouts & quizzes',

    'workspace.common_title': '✦ Common Teaching Settings (Applied across all 3 modules)',
    'workspace.generate_all': '🚀 Generate Complete Package (Handout + Deck + Quiz)',
    'handout.badge': '📝 Module 1',
    'handout.title': 'Lesson Handout',
    'handout.desc': 'A4 study guide, core takeaways & review notes',
    'handout.audience': 'Target Audience',
    'handout.detail': 'Detail Level',
    'handout.web_search': 'Enable Web Search (Add current cases)',
    'handout.btn_to_workbench': '🎯 Reference Handout in Workspace',
    'handout.btn_print': '🖨️ A4 Preview & Print (PDF)',
    'handout.btn_download_docx': '📄 Download Word (.docx)',
    'handout.btn': '📝 Generate A4 Handout',
    'deck.badge': '🎯 Module 2',
    'deck.title': 'Teaching Deck',
    'deck.desc': 'Slide outlines, visual diagrams & speaker scripts',
    'deck.web_search': 'Enable Web Search (Supplement cases & data)',
    'deck.btn': '✦ Generate Slide Deck',
    'deck.btn_pdf': '📑 Download Deck (PDF)',
    'deck.btn_pptx': '📊 Download Deck (.pptx)',
    'deck.btn_print_handout': '🖨️ Speaker Notes Print (PDF)',
    'deck.btn_docx': '📄 Download Notes (.docx)',
    'deck.btn_download_docx': '📄 Download Notes (.docx)',
    'quiz.badge': '📑 Module 3',
    'quiz.title': 'Unit Quiz',
    'quiz.desc': 'Unit assessment, distractor options & explanations',
    'quiz.count': 'Question Count',
    'quiz.difficulty': 'Difficulty',
    'quiz.web_search': 'Enable Question Search (Real exams & questions)',
    'quiz.btn': '📑 Generate Unit Quiz',
    'quiz.teacher_mode_toggle': '✔ Show Answers & Explanations (Teacher Mode)',
    'quiz.btn_print': '🖨️ Print Quiz (PDF)',
    'quiz.btn_download_docx': '📄 Download Quiz (.docx)',

    'opt.audience.college': 'College Students',
    'opt.audience.high': 'High School Students',
    'opt.audience.middle': 'Middle School Students',
    'opt.audience.elementary': 'Elementary School Students',
    'opt.audience.adult': 'Working Adults',
    'opt.audience.general': 'General Public',
    'opt.tone.clear': 'Clear & Easy to Understand',
    'opt.tone.lively': 'Lively & Interactive',
    'opt.tone.rigorous': 'Professional & Rigorous',
    'opt.tone.story': 'Story-driven',

    'opt.handout_aud.student': 'Students / Learners',
    'opt.handout_aud.instructor': 'Instructor Lesson Prep',
    'opt.handout_aud.pro': 'Professional Trainees',
    'opt.handout_aud.self': 'Self-Learners',

    'opt.handout_det.concise': 'Concise Summary (Quick)',
    'opt.handout_det.standard': 'Standard Guide (Balanced)',
    'opt.handout_det.detailed': 'In-depth Analysis (Detailed)',

    'opt.quiz_cnt.3': '3 Questions (Quick check)',
    'opt.quiz_cnt.5': '5 Questions (Standard quiz)',
    'opt.quiz_cnt.8': '8 Questions (Unit test)',
    'opt.quiz_cnt.10': '10 Questions (Comprehensive)',

    'opt.quiz_diff.all': 'Mixed (Progressive)',
    'opt.quiz_diff.easy': 'Basic Concepts',
    'opt.quiz_diff.medium': 'Moderate Understanding',
    'opt.quiz_diff.hard': 'Advanced & Problem Solving',

    'opt.provider.gemini': 'Gemini Cloud API ✨',
    'opt.provider.ollama_cloud': 'Ollama Cloud API',
    'opt.provider.ollama_local': 'Ollama Local LLM',
    'opt.provider.openai': 'OpenAI Cloud API',

    'opt.duration.20': '20 Mins',
    'opt.duration.30': '30 Mins',
    'opt.duration.45': '45 Mins',
    'opt.duration.60': '60 Mins',
    'opt.duration.90': '90 Mins',

    'opt.slides.6': '6 Slides',
    'opt.slides.8': '8 Slides',
    'opt.slides.10': '10 Slides',
    'opt.slides.12': '12 Slides',
    'opt.slides.15': '15 Slides',

    'opt.lang.zh_tw': '🇹🇼 Traditional Chinese',
    'opt.lang.en': '🇺🇸 English',
    'opt.lang.auto': '🤖 Auto (Match Material)',

    'deck.eyebrow': 'Lesson Content Ready',
    'deck.title': 'Teaching Deck',
    'deck.subtitle': 'Upload materials to start generating.',
    'deck.btn_pdf': '📑 Download Deck (PDF)',
    'deck.btn_script': '🖨️ Speaker Notes Print (PDF)',
    'deck.btn_pptx': '📊 Download Deck (.pptx)',
    'deck.empty_slide': 'No slides yet',
    'deck.stage_empty_b': 'No Content Generated',
    'deck.stage_empty_s': 'Return to workspace to upload PDF & configure course',
    'deck.preview_empty_b': 'No Slide Deck Generated Yet',
    'deck.preview_empty_s': 'Click "✦ Generate Slide Deck" or "🚀 Generate All Items" in Workspace.',
    'deck.preview_empty_btn': '← Go to Workspace',
    'deck.notes_label': 'Speaker Notes',
    'deck.page_ref': 'Notes',
    'deck.speaker_notes_placeholder': 'Speaker notes for each slide will appear here.',

    'chat.eyebrow': 'Document Knowledge Base',
    'chat.title': 'Ask Your PDF, Not The Web.',
    'chat.subtitle': 'Every answer is grounded in your document with page citations.',
    'chat.doc_empty_b': 'No Material Selected',
    'chat.doc_empty_s': 'Please upload a PDF in workspace first',
    'chat.welcome_b': "Hi! I'm your Lesson Assistant",
    'chat.welcome_p': 'Once a document is uploaded, ask me to explain concepts, compare ideas, or summarize key points.',
    'chat.sug_1': 'What are the 3 core takeaways of this material?',
    'chat.sug_2': 'Explain the main concept with a simple example',
    'chat.web_search': 'Enable Web Search (Search web if answer is not in PDF)',
    'chat.placeholder': 'Ask questions about the document...',
    'chat.shortcut': '<span>↵</span> Enter to send · Shift + Enter for new line',

    'admin.eyebrow': 'Permissions & User Management',
    'admin.title': '👑 Admin Console',
    'admin.subtitle': 'Review registered accounts, modify permissions, reset passwords, and manage users.',
    'admin.btn_create_user': '➕ Add User / Admin',
    'admin.metric_total': 'Total Accounts',
    'admin.metric_pending': 'Pending Approval',
    'admin.metric_admin': 'System Admins',
    'admin.th_id': 'ID',
    'admin.th_username': 'Username',
    'admin.th_tier': 'Membership Tier / Role',
    'admin.th_daily_usage': 'Daily Usage / Quota',
    'admin.th_total_usage': 'Cumulative Usage',
    'admin.th_last_login': 'Last Active Time',
    'admin.th_role': 'Role',
    'admin.th_status': 'Status',
    'admin.th_created': 'Created At',
    'admin.th_actions': 'Actions',
    'admin.loading': 'Loading...',
    'admin.create_modal_title': '➕ Create Account (Admin Pre-approved)',
    'admin.create_modal_sub': 'Directly create pre-approved regular user or admin accounts.',
    'admin.create_lbl_username': 'Username',
    'admin.create_lbl_password': 'Password',
    'admin.create_lbl_role': 'Account Role',
    'admin.create_lbl_tier': 'Membership Tier',
    'admin.create_btn_submit': 'Confirm Create Account',
    'admin.opt_role_user': '👤 Regular User',
    'admin.opt_role_admin': '👑 System Admin',
    'admin.opt_tier_trial': '🎓 Teacher Free Trial (100 pts/day)',
    'admin.opt_tier_pro': '⭐ Teacher Pro (1,000 pts/day)',
    'admin.opt_tier_inst': '🏫 Institution / School (10,000 pts/day)',

    'profile.eyebrow': 'Account & Security Settings',
    'profile.title': '⚙️ Account Settings',
    'profile.subtitle': 'View account identity, daily quota usage, and change password.',
    'profile.basic_title': 'Basic Account Info',
    'profile.role_user': 'Regular User',
    'profile.role_admin': 'System Admin',
    'profile.lbl_username': 'Username',
    'profile.lbl_role': 'Role',
    'profile.lbl_quota': 'Daily Quota',
    'profile.btn_logout': 'Log Out',
    'profile.change_pass_title': 'Change Password',
    'profile.lbl_old_pass': 'Current Password',
    'profile.lbl_new_pass': 'New Password',
    'profile.ph_old_pass': 'Enter current password',
    'profile.ph_new_pass': 'Enter new password (at least 4 chars)',
    'profile.btn_save_pass': 'Save New Password',

    'auth.tab_login': 'User Login',
    'auth.tab_register': 'Register',
    'auth.login_title': 'Welcome Back',
    'auth.login_sub': 'Please enter your credentials to access API features & quota',
    'auth.lbl_username': 'Username',
    'auth.lbl_password': 'Password',
    'auth.ph_username': 'Enter username',
    'auth.ph_password': 'Enter password',
    'auth.btn_login': 'Sign In',
    'auth.reg_title': 'Create Account',
    'auth.reg_sub': 'Registration requires admin approval before logging in.',
    'auth.ph_reg_user': 'At least 3 characters',
    'auth.ph_reg_pass': 'At least 4 characters',
    'auth.btn_register': 'Submit Registration',

    'loading.read_title': 'Reading Your Material',
    'loading.read_copy': 'Analyzing chapters and key concepts...',
    'loading.read_multimodal_copy': 'Analyzing figures, tables & math formulas, this may take a moment...',
    'loading.read_fast_copy': 'Fast reading plain text and section structure...',
    'loading.deck_title': 'Designing Lesson Deck & Scripts...',
    'loading.deck_copy': 'Using LLM to structure lesson flow & generate slides, takes a few minutes...',
    'loading.ask_title': 'Searching PDF & Generating Answer...',
    'loading.ask_copy': 'Indexing document chunks precisely with page citations...',
    'toast.logout': 'Logged out successfully',
    'toast.pass_changed': 'Password changed successfully',
    'toast.pdf_invalid': 'Please select a valid PDF file',
    'toast.pdf_uploaded': 'Material parsed successfully! Ready for deck & Q&A.',

    'stepper.step1_title': 'Upload / Brainstorm',
    'stepper.step1_sub': 'PDF / AI Assistant',
    'stepper.step2_title': 'Set Audience & Tone',
    'stepper.step2_sub': 'Global Parameters',
    'stepper.step3_title': 'Generate Handout',
    'stepper.step3_sub': 'Core Knowledge Base',
    'stepper.step4_title': 'Derive Deck & Quiz',
    'stepper.step4_sub': 'Slides & Quizzes',
    'workspace.generate_all': '🚀 Generate Full Suite (Handout ➔ Deck & Quiz)',
    'handout.badge': '📝 Module 1',
    'deck.badge': '🎯 Module 2',
    'quiz.badge': '📑 Module 3',
    'profile.top_badge': 'Account Center',
    'profile.btn_refresh': 'Refresh Info',
    'toast.profile_refreshed': 'Account info updated',

    'footer.copyright': '© 2026 ArchCet. All rights reserved.',
    'footer.terms': 'Terms of Service',
    'footer.privacy': 'Privacy Policy',
    'footer.contact': 'Contact'
  }
};

function t(key) {
  const lang = state.lang || 'zh-TW';
  return (translations[lang] && translations[lang][key]) || (translations['zh-TW'] && translations['zh-TW'][key]) || key;
}

function setLanguage(lang) {
  state.lang = lang;
  localStorage.setItem('app_lang', lang);
  document.documentElement.lang = lang === 'en' ? 'en' : 'zh-TW';

  $$('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const translated = t(key);
    if (translated) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translated;
      } else {
        el.innerHTML = translated;
      }
    }
  });

  updateSelectOptions();

  if (state.provider) {
    updateProviderUI({ provider: state.provider });
  }

  if (state.user) {
    updateAuthUI(state.user);
  } else {
    updateAuthUI(null);
  }

  const activeView = $('.view.active')?.id.replace('View', '') || 'home';
  switchView(activeView);
}

function updateSelectOptions() {
  const audienceSelect = $('#audience');
  if (audienceSelect) {
    const selectedVal = audienceSelect.value;
    const audienceOpts = [
      { val: '大學生', key: 'opt.audience.college' },
      { val: '高中生', key: 'opt.audience.high' },
      { val: '國中生', key: 'opt.audience.middle' },
      { val: '國小生', key: 'opt.audience.elementary' },
      { val: '職場成人', key: 'opt.audience.adult' },
      { val: '一般大眾', key: 'opt.audience.general' }
    ];
    audienceSelect.innerHTML = audienceOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const toneSelect = $('#tone');
  if (toneSelect) {
    const selectedVal = toneSelect.value;
    const toneOpts = [
      { val: '清楚易懂', key: 'opt.tone.clear' },
      { val: '活潑互動', key: 'opt.tone.lively' },
      { val: '專業嚴謹', key: 'opt.tone.rigorous' },
      { val: '故事引導', key: 'opt.tone.story' }
    ];
    toneSelect.innerHTML = toneOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const providerSelect = $('#providerSelect');
  if (providerSelect) {
    const selectedVal = providerSelect.value;
    const providerOpts = [
      { val: 'gemini', key: 'opt.provider.gemini' },
      { val: 'ollama_cloud', key: 'opt.provider.ollama_cloud' },
      { val: 'ollama_local', key: 'opt.provider.ollama_local' },
      { val: 'openai', key: 'opt.provider.openai' }
    ];
    providerSelect.innerHTML = providerOpts.map(o =>
      `<option value="${o.val}" style="font-size: 12px !important;" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const durationSelect = $('#duration');
  if (durationSelect) {
    const selectedVal = durationSelect.value;
    const durationOpts = [
      { val: '20', key: 'opt.duration.20' },
      { val: '30', key: 'opt.duration.30' },
      { val: '45', key: 'opt.duration.45' },
      { val: '60', key: 'opt.duration.60' },
      { val: '90', key: 'opt.duration.90' }
    ];
    durationSelect.innerHTML = durationOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const slideCountSelect = $('#slideCount');
  if (slideCountSelect) {
    const selectedVal = slideCountSelect.value;
    const slideOpts = [
      { val: '6', key: 'opt.slides.6' },
      { val: '8', key: 'opt.slides.8' },
      { val: '10', key: 'opt.slides.10' },
      { val: '12', key: 'opt.slides.12' },
      { val: '15', key: 'opt.slides.15' }
    ];
    slideCountSelect.innerHTML = slideOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const targetLangSelect = $('#targetLanguage');
  if (targetLangSelect) {
    const selectedVal = targetLangSelect.value;
    const langOpts = [
      { val: 'auto', key: 'opt.lang.auto' },
      { val: 'zh-TW', key: 'opt.lang.zh_tw' },
      { val: 'en', key: 'opt.lang.en' }
    ];
    targetLangSelect.innerHTML = langOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const handoutAudienceSelect = $('#handoutAudience');
  if (handoutAudienceSelect) {
    const selectedVal = handoutAudienceSelect.value;
    const audOpts = [
      { val: '學生/學習者', key: 'opt.handout_aud.student' },
      { val: '授課講師備課用', key: 'opt.handout_aud.instructor' },
      { val: '職場專業培訓學員', key: 'opt.handout_aud.pro' },
      { val: '自學者筆記', key: 'opt.handout_aud.self' }
    ];
    handoutAudienceSelect.innerHTML = audOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const handoutDetailSelect = $('#handoutDetail');
  if (handoutDetailSelect) {
    const selectedVal = handoutDetailSelect.value;
    const detOpts = [
      { val: 'concise', key: 'opt.handout_det.concise' },
      { val: 'standard', key: 'opt.handout_det.standard' },
      { val: 'detailed', key: 'opt.handout_det.detailed' }
    ];
    handoutDetailSelect.innerHTML = detOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const quizCountSelect = $('#quizCount');
  if (quizCountSelect) {
    const selectedVal = quizCountSelect.value;
    const countOpts = [
      { val: '3', key: 'opt.quiz_cnt.3' },
      { val: '5', key: 'opt.quiz_cnt.5' },
      { val: '8', key: 'opt.quiz_cnt.8' },
      { val: '10', key: 'opt.quiz_cnt.10' }
    ];
    quizCountSelect.innerHTML = countOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }

  const quizDiffSelect = $('#quizDifficulty');
  if (quizDiffSelect) {
    const selectedVal = quizDiffSelect.value;
    const diffOpts = [
      { val: 'all', key: 'opt.quiz_diff.all' },
      { val: 'easy', key: 'opt.quiz_diff.easy' },
      { val: 'medium', key: 'opt.quiz_diff.medium' },
      { val: 'hard', key: 'opt.quiz_diff.hard' }
    ];
    quizDiffSelect.innerHTML = diffOpts.map(o =>
      `<option value="${o.val}" ${o.val === selectedVal ? 'selected' : ''}>${t(o.key)}</option>`
    ).join('');
  }
}

function translateError(msg) {
  if (!msg) return state.lang === 'en' ? 'Service temporarily unavailable' : '服務暫時無法使用';
  if (state.lang !== 'en') return msg;

  const errorMap = {
    '服務暫時無法使用': 'Service temporarily unavailable',
    '只支援 PDF 檔案': 'Only PDF files are supported',
    '找不到文件，請重新上傳': 'Document not found, please re-upload',
    '找不到簡報': 'Presentation deck not found',
    '找不到講稿': 'Speaker script not found',
    '請先登入帳號': 'Please log in first',
    '僅限管理員存取': 'Admin access only',
    '僅限管理員存取控制台': 'Admin access only',
    '請輸入有效的帳號與密碼': 'Please enter a valid username and password',
    '帳號與密碼長度至少需 4 個字元': 'Username and password must be at least 4 characters',
    '帳號或密碼錯誤': 'Incorrect username or password',
    '帳號尚未經過管理員核准開通': 'Account pending admin approval',
    '此帳號已被停用': 'Account has been disabled',
    '此帳號已被停用或拒絕開通': 'Account disabled or application rejected',
    '使用者名稱已存在': 'Username already exists',
    '無效的 Token': 'Invalid authentication token',
    '登入憑證已過期': 'Session expired, please log in again',
    '每日生成簡報配額已達上限 (每日最多 3 份)': 'Daily deck quota reached (Max 3/day)',
    '每日文件提問配額已達上限 (每日最多 10 次)': 'Daily Q&A quota reached (Max 10/day)',
    '新密碼長度至少需 4 個字元': 'New password must be at least 4 characters',
    '舊密碼輸入錯誤': 'Incorrect old password',
    '密碼已成功修改': 'Password changed successfully',
    '未設定 OPENAI_API_KEY，無法切換至 OpenAI': 'OPENAI_API_KEY is not set. Cannot switch to OpenAI.',
    '無法讀取加密的 PDF': 'Cannot read encrypted PDF files.',
    'PDF 沒有可擷取的文字；掃描檔請先執行 OCR': 'PDF has no extractable text; please run OCR for scanned documents first.',
    '請先選擇 PDF 檔案': 'Please select a PDF file',
    '請選擇 PDF 檔案': 'Please select a PDF file',
    '請先登入帳號以開始問答': 'Please log in to ask questions',
    '請先上傳教材': 'Please upload material first',
    '請先登入帳號以使用文件上傳功能': 'Please log in to upload documents',
    '登入失敗': 'Login failed',
    '註冊失敗': 'Registration failed',
    '用戶狀態已更新': 'User status updated',
    '角色權限已更新': 'User role updated',
    '密碼重置成功': 'Password reset successfully',
    '已刪除使用者': 'User deleted successfully'
  };

  if (errorMap[msg]) return errorMap[msg];

  if (typeof msg === 'string') {
    if (msg.includes('未偵測到 Ollama 本機服務') || msg.includes('未偵測到 Ollama')) {
      const match = msg.match(/\((http[s]?:\/\/[^\)]+)\)/);
      const url = match ? match[1] : 'http://localhost:11434';
      return `Local Ollama service not detected. Please verify Ollama is installed and running at ${url}.`;
    }
    if (msg.includes('檔案不可超過')) {
      return msg.replace('檔案不可超過', 'File size cannot exceed');
    }
    if (msg.includes('處理 PDF 時發生錯誤')) {
      return msg.replace('處理 PDF 時發生錯誤：', 'Error processing PDF: ');
    }
    if (msg.includes('AI 暫時無法回答')) {
      return msg.replace('AI 暫時無法回答：', 'AI temporarily unavailable: ');
    }
    if (msg.includes('產生教材時發生錯誤')) {
      return msg.replace('產生教材時發生錯誤：', 'Error generating lesson content: ');
    }
    if (msg.includes('Hugging Face embedding 模型載入或推論失敗')) {
      return msg.replace('Hugging Face embedding 模型載入或推論失敗：', 'Hugging Face embedding model load/inference failed: ');
    }
  }

  return msg;
}

function toast(message, error = false) {
  message = translateError(message);
  const el = $('#toast'); el.querySelector('p').textContent = message; el.querySelector('span').textContent = error ? '!' : '✓';
  el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 3200);
}

let loadingTimer = null;
function loading(show, title, copy, progressSteps = []) {
  if (loadingTimer) {
    clearInterval(loadingTimer);
    loadingTimer = null;
  }
  title = title || t('loading.read_title');
  copy = copy || t('loading.read_copy');
  const titleEl = $('#loadingTitle');
  const copyEl = $('#loadingCopy');
  const overlayEl = $('#loadingOverlay');
  if (titleEl) titleEl.textContent = title;
  if (copyEl) copyEl.textContent = copy;
  if (overlayEl) overlayEl.classList.toggle('hidden', !show);

  if (show && progressSteps && progressSteps.length > 0) {
    let stepIdx = 0;
    loadingTimer = setInterval(() => {
      stepIdx = (stepIdx + 1) % progressSteps.length;
      if (copyEl) {
        copyEl.textContent = progressSteps[stepIdx];
      }
    }, 2800);
  }
}

// 支援 Bearer Token 的 Fetch 封裝
async function api(path, options = {}) {
  const token = localStorage.getItem('auth_token');
  options.headers = options.headers || {};
  if (token) {
    if (options.body instanceof FormData) {
      options.headers['Authorization'] = `Bearer ${token}`;
    } else {
      options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    }
  }

  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    let errorMsg = body.detail;
    if (typeof errorMsg === 'object' && errorMsg !== null) {
      errorMsg = JSON.stringify(errorMsg);
    }
    if (!errorMsg) {
      errorMsg = response.status === 503
        ? '服務暫時無法使用'
        : `HTTP Error ${response.status}: ${response.statusText || '系統發生錯誤'}`;
    }

    if (response.status === 401 && token) {
      logoutUser(false);
      openAuthModal('login');
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

// --- 身份驗證 UI 與 Tier 配額控制 ---

function getTierInfo(user) {
  const isEn = state.lang === 'en';
  if (!user) {
    return {
      tierKey: 'teacher_trial',
      badge: isEn ? '🎓 Teacher Free Trial' : '🎓 教師試用版',
      deckLimit: 1,
      handoutLimit: 2,
      quizLimit: 3,
      askLimit: 10,
      uploadLimit: 5,
      maxUploadMb: 10,
      isUnlimited: false
    };
  }
  if (user.role === 'admin' || user.tier === 'admin') {
    return {
      tierKey: 'admin',
      badge: isEn ? '👑 Unlimited' : '👑 無限版',
      deckLimit: -1,
      handoutLimit: -1,
      quizLimit: -1,
      askLimit: -1,
      uploadLimit: -1,
      maxUploadMb: 500,
      isUnlimited: true
    };
  }
  let rawTier = (user.tier || '').toLowerCase();
  if (rawTier.includes('inst') || rawTier.includes('school')) rawTier = 'institution';
  else if (rawTier.includes('pro')) rawTier = 'teacher_pro';
  else if (rawTier.includes('trial') || rawTier.includes('free')) rawTier = 'teacher_trial';

  const tierKey = rawTier || (user.role === 'admin' ? 'admin' : 'teacher_trial');
  const tiers = {
    'teacher_trial': {
      tierKey: 'teacher_trial',
      badge: isEn ? '🎓 Teacher Free Trial' : '🎓 教師試用版',
      deckLimit: 1,
      handoutLimit: 2,
      quizLimit: 3,
      askLimit: 10,
      uploadLimit: 5,
      maxUploadMb: 10,
      isUnlimited: false
    },
    'teacher_pro': {
      tierKey: 'teacher_pro',
      badge: isEn ? '⭐ Teacher Pro' : '⭐ 教師專業版',
      deckLimit: 10,
      handoutLimit: 15,
      quizLimit: 20,
      askLimit: 50,
      uploadLimit: 20,
      maxUploadMb: 30,
      isUnlimited: false
    },
    'institution': {
      tierKey: 'institution',
      badge: isEn ? '🏫 Institution / School' : '🏫 機構/學校版',
      deckLimit: 100,
      handoutLimit: 150,
      quizLimit: 200,
      askLimit: 500,
      uploadLimit: 100,
      maxUploadMb: 100,
      isUnlimited: false
    }
  };
  return tiers[tierKey] || tiers['teacher_pro'];
}

function updateFeaturePermissionsUI(user) {
  const isEn = state.lang === 'en';
  const tierKey = user?.tier || (user?.role === 'admin' ? 'admin' : 'teacher_trial');
  const tierInfo = user?.tier_info || {};

  const enableVlm = tierInfo.enable_vlm !== undefined
    ? tierInfo.enable_vlm
    : (user != null && (tierKey === 'teacher_pro' || tierKey === 'institution' || tierKey === 'admin' || user.role === 'admin'));

  const enableWebSearch = tierInfo.enable_web_search !== undefined
    ? tierInfo.enable_web_search
    : (user != null && (tierKey === 'teacher_pro' || tierKey === 'institution' || tierKey === 'admin' || user.role === 'admin'));

  // 1. Multimodal VLM Toggle (#multimodalToggle)
  const multimodalToggle = $('#multimodalToggle');
  const multimodalCard = $('.multimodal-card');
  let vlmBadge = $('#vlmLockBadge');

  if (multimodalToggle) {
    if (!enableVlm) {
      multimodalToggle.checked = false;
      multimodalToggle.disabled = true;
      if (multimodalCard) multimodalCard.classList.add('feature-locked');

      if (!vlmBadge) {
        vlmBadge = document.createElement('small');
        vlmBadge.id = 'vlmLockBadge';
        vlmBadge.className = 'lock-badge';
        vlmBadge.style.cssText = 'color: #d97706; font-weight: 600; display: block; margin-top: 4px; font-size: 11px;';
        const toggleText = $('.multimodal-card .toggle-text');
        if (toggleText) toggleText.appendChild(vlmBadge);
      }
      vlmBadge.textContent = isEn ? '🔒 Teacher Pro Exclusive (Diagrams & Math Formulas)' : '🔒 ⭐ 教師專業版獨享 (圖表與公式解析)';
      vlmBadge.style.display = 'block';
    } else {
      multimodalToggle.disabled = false;
      if (multimodalCard) multimodalCard.classList.remove('feature-locked');
      if (vlmBadge) vlmBadge.style.display = 'none';
    }
  }

  // 2. Web Search Checkboxes (#deckWebSearch, #handoutWebSearch, #quizWebSearch, #qaWebSearch)
  const searchCheckboxes = [
    { el: $('#deckWebSearch'), badgeId: 'deckWebSearchLockBadge' },
    { el: $('#handoutWebSearch'), badgeId: 'handoutWebSearchLockBadge' },
    { el: $('#quizWebSearch'), badgeId: 'quizWebSearchLockBadge' },
    { el: $('#qaWebSearch'), badgeId: 'qaWebSearchLockBadge' }
  ];

  searchCheckboxes.forEach(({ el: chk, badgeId }) => {
    if (!chk) return;
    let badge = $(`#${badgeId}`);
    if (!enableWebSearch) {
      chk.checked = false;
      chk.disabled = true;
      if (!badge) {
        badge = document.createElement('span');
        badge.id = badgeId;
        badge.className = 'lock-badge-inline';
        badge.style.cssText = 'color: #d97706; font-weight: 600; margin-left: 6px; font-size: 11px;';
        const parent = chk.closest('label');
        if (parent) parent.appendChild(badge);
      }
      badge.textContent = isEn ? '🔒 Pro Exclusive' : '🔒 ⭐ 專業版獨享';
      badge.style.display = 'inline';
    } else {
      chk.disabled = false;
      if (badge) badge.style.display = 'none';
    }
  });
}

function updateAuthUI(user) {
  state.user = user;
  const container = $('#authHeaderContainer');
  const tier = getTierInfo(user);

  if (user) {
    const q = user.quota || {};
    const isUnlimited = tier.isUnlimited;

    const deckLimit = isUnlimited ? -1 : (q.deck?.daily_limit || tier.deckLimit);
    const handoutLimit = isUnlimited ? -1 : (q.handout?.daily_limit || tier.handoutLimit);
    const quizLimit = isUnlimited ? -1 : (q.quiz?.daily_limit || tier.quizLimit);
    const askLimit = isUnlimited ? -1 : (q.ask?.daily_limit || tier.askLimit);
    const credits = user.credits || {
      used: q.credits?.used_count || 0,
      daily_limit: q.credits?.daily_limit || (isUnlimited ? -1 : 100),
      remaining: q.credits?.remaining || (isUnlimited ? -1 : 100),
      is_unlimited: isUnlimited
    };
    const remCredits = isUnlimited ? -1 : (credits.remaining !== undefined ? credits.remaining : 100);
    const limCredits = isUnlimited ? -1 : (credits.daily_limit || 100);

    const quotaLabel = isUnlimited
      ? tier.badge
      : (state.lang === 'en'
        ? `${tier.badge} · ${remCredits}/${limCredits} pts`
        : `${tier.badge} · 剩餘 ${remCredits}/${limCredits} 點`);

    if (container) {
      container.innerHTML = `
        <div class="auth-user-chip">
          <strong>👤 ${escapeHtml(user.username)}</strong>
          <small>${quotaLabel}</small>
          <button class="auth-logout-btn" id="logoutBtn" type="button">${t('topbar.logout')}</button>
        </div>
      `;
    }

    if ($('#quotaBadge')) $('#quotaBadge').textContent = tier.badge;
    if ($('#creditBalanceText')) {
      $('#creditBalanceText').textContent = isUnlimited
        ? (state.lang === 'en' ? 'Unlimited' : '無限點數')
        : (state.lang === 'en' ? `${remCredits} / ${limCredits} pts` : `${remCredits} / ${limCredits} 點`);
    }
    if ($('#creditUsageBar')) {
      const pct = isUnlimited ? 100 : Math.min(100, Math.max(0, (remCredits / (limCredits || 1)) * 100));
      $('#creditUsageBar').style.width = `${pct}%`;
      $('#creditUsageBar').style.background = isUnlimited ? '#d97706' : (remCredits <= 10 ? '#ef4444' : 'linear-gradient(90deg, #10b981, #059669)');
    }

    if ($('#userAvatar')) $('#userAvatar').textContent = user.role === 'admin' ? '👑' : user.username.charAt(0).toUpperCase();
    if ($('#userProfileInfo')) $('#userProfileInfo').innerHTML = `${escapeHtml(user.username)}<small>${tier.badge}</small>`;
  } else {
    if (container) container.innerHTML = `<button class="auth-btn" id="openAuthBtn" type="button" data-i18n="topbar.login_reg">${t('topbar.login_reg')}</button>`;

    if ($('#quotaBadge')) $('#quotaBadge').textContent = tier.badge;
    if ($('#creditBalanceText')) $('#creditBalanceText').textContent = state.lang === 'en' ? `- / 100 pts` : `- / 100 點`;
    if ($('#creditUsageBar')) $('#creditUsageBar').style.width = '0%';

    if ($('#userAvatar')) $('#userAvatar').textContent = state.lang === 'en' ? 'G' : '客';
    if ($('#userProfileInfo')) $('#userProfileInfo').innerHTML = `${t('quota.guest')}<small>${tier.badge}</small>`;
  }

  // 更新首頁 Portal 卡片 (訪客登入區 vs 已登入歡迎區)
  const guestPortal = $('#homeGuestPortal');
  const userPortal = $('#homeUserPortal');
  if (guestPortal && userPortal) {
    if (user) {
      guestPortal.classList.add('hidden');
      userPortal.classList.remove('hidden');
      if ($('#homeWelcomeUsername')) $('#homeWelcomeUsername').textContent = user.username;
      if ($('#homeWelcomeRoleBadge')) {
        $('#homeWelcomeRoleBadge').textContent = tier.badge;
        $('#homeWelcomeRoleBadge').className = `role-chip ${user.role}`;
      }
      if ($('#homeWelcomeAvatar')) {
        $('#homeWelcomeAvatar').textContent = user.role === 'admin' ? '👑' : user.username.charAt(0).toUpperCase();
      }
      if ($('#homeWelcomeQuota')) {
        const isUnlimited = tier.isUnlimited;
        const credits = user.credits || { remaining: 100, daily_limit: 100 };
        $('#homeWelcomeQuota').textContent = isUnlimited
          ? (state.lang === 'en' ? 'Unlimited credits' : '無限點數')
          : (state.lang === 'en' ? `Today's remaining: ${credits.remaining !== undefined ? credits.remaining : 100} / ${credits.daily_limit || 100} pts` : `今日剩餘點數：${credits.remaining !== undefined ? credits.remaining : 100} / ${credits.daily_limit || 100} 點`);
      }
    } else {
      guestPortal.classList.remove('hidden');
      userPortal.classList.add('hidden');
    }
  }

  updateAdminUI();
  updateAgentDepartmentBadges(user);
  updateFeaturePermissionsUI(user);
  const profileNavBtn = $('#profileNavBtn');
  if (profileNavBtn) {
    if (state.user) profileNavBtn.classList.remove('hidden');
    else profileNavBtn.classList.add('hidden');
  }
}

function renderDeptActiveIndicators() {
  const activeKey = state.activeDept; // null = unsegmented omni mode

  const depts = [
    { key: 'academic', card: '#deptCardAcademic' },
    { key: 'marketing', card: '#deptCardMarketing' },
    { key: 'operations', card: '#deptCardOperations' },
    { key: 'devops', card: '#deptCardDevops' }
  ];

  depts.forEach(item => {
    const card = $(item.card);
    if (!card) return;
    const isThisActive = (activeKey === item.key);

    if (isThisActive) {
      card.classList.add('dept-card-active');
    } else {
      card.classList.remove('dept-card-active');
    }
  });
  if (typeof updateAgentDeptBar === 'function') {
    updateAgentDeptBar(activeKey);
  }
}

function updateAgentDepartmentBadges(user) {
  const isEn = state.lang === 'en';
  const role = user?.role || 'guest';
  const tierKey = user?.tier || (role === 'admin' ? 'admin' : 'teacher_trial');
  const isAdmin = role === 'admin' || tierKey === 'admin';

  function setCardStatus(cardSelector, isActive) {
    const card = $(cardSelector);
    if (!card) return;
    card.setAttribute('data-disabled', (!isActive).toString());
  }

  // 1. 教務教學部 (Academic)
  const academicBadge = $('#deptBadgeAcademic');
  if (academicBadge) {
    academicBadge.className = 'dept-badge badge-active';
    academicBadge.textContent = isEn ? '🟢 Active' : '🟢 已啟用';
  }
  setCardStatus('#deptCardAcademic', true);

  // 2. 市場與營銷部 (Marketing)
  const mktCard = $('#deptCardMarketing');
  const mktBadge = $('#deptBadgeMarketing');
  if (mktBadge) {
    mktBadge.className = 'dept-badge badge-active';
    mktBadge.textContent = isEn ? '🟢 Active' : '🟢 已啟用';
    if (mktCard) mktCard.style.opacity = '1';
  }
  setCardStatus('#deptCardMarketing', true);

  // 3. 營運與行政部 (Operations)
  const opsCard = $('#deptCardOperations');
  const opsBadge = $('#deptBadgeOperations');
  if (opsBadge) {
    opsBadge.className = 'dept-badge badge-active';
    opsBadge.textContent = isEn ? '🟢 Active' : '🟢 已啟用';
    if (opsCard) opsCard.style.opacity = '1';
  }
  setCardStatus('#deptCardOperations', true);

  // 4. 技術維護部 (DevOps) - Admin Only (Far right)
  const devopsCard = $('#deptCardDevops');
  const devopsBadge = $('#deptBadgeDevops');
  if (devopsBadge) {
    if (isAdmin) {
      devopsBadge.className = 'dept-badge badge-active';
      devopsBadge.textContent = isEn ? '🟢 Active' : '🟢 已啟用';
      if (devopsCard) devopsCard.style.opacity = '1';
    } else {
      devopsBadge.className = 'dept-badge badge-locked';
      devopsBadge.textContent = isEn ? '🔒 Admin Only' : '🔒 👑 管理員專用';
      if (devopsCard) devopsCard.style.opacity = '0.7';
    }
  }
  setCardStatus('#deptCardDevops', isAdmin);
  renderDeptActiveIndicators();
}

async function fetchCurrentUser() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    updateAuthUI(null);
    return;
  }
  try {
    const user = await api('/api/user/me');
    updateAuthUI(user);
  } catch (err) {
    localStorage.removeItem('auth_token');
    updateAuthUI(null);
  }
}

function logoutUser(notify = true) {
  localStorage.removeItem('auth_token');
  updateAuthUI(null);
  if (notify) toast(t('toast.logout'));
}

// Modal 控制
function openAuthModal(tab = 'login') {
  switchAuthTab(tab);
  $('#loginError').classList.add('hidden');
  $('#regError').classList.add('hidden');
  $('#regSuccess').classList.add('hidden');
  const modal = $('#authModal');
  modal.classList.remove('hidden');
}

function closeAuthModal() {
  $('#authModal').classList.add('hidden');
}

function switchAuthTab(tab) {
  const isLogin = tab === 'login';
  $('#tabLoginBtn').classList.toggle('active', isLogin);
  $('#tabRegisterBtn').classList.toggle('active', !isLogin);
  $('#loginForm').classList.toggle('hidden', !isLogin);
  $('#registerForm').classList.toggle('hidden', isLogin);
}

// 事件委派：點擊登入按鈕、登出按鈕、語言切換或側邊欄
document.addEventListener('click', (e) => {
  const lockedMultimodal = e.target.closest('.multimodal-card.feature-locked');
  if (lockedMultimodal) {
    toast(state.lang === 'en' ? '🔒 PDF Reading Mode (VLM) is exclusive to Teacher Pro tier or higher!' : '🔒 📷 「圖表與公式解析」為「⭐ 教師專業版」解鎖功能！');
    return;
  }

  const lockedWebSearchLabel = e.target.closest('label:has(#deckWebSearch:disabled), label:has(#qaWebSearch:disabled)');
  if (lockedWebSearchLabel || (e.target.id === 'deckWebSearch' && e.target.disabled) || (e.target.id === 'qaWebSearch' && e.target.disabled)) {
    toast(state.lang === 'en' ? '🔒 Web Search is exclusive to Teacher Pro tier or higher!' : '🔒 🌐 「網路補充搜尋」為「⭐ 教師專業版」解鎖功能！');
    return;
  }

  const langBtn = e.target.closest('.lang-btn');
  if (langBtn) {
    e.preventDefault();
    setLanguage(langBtn.dataset.lang);
    return;
  }

  const openBtn = e.target.closest('#openAuthBtn') || e.target.closest('.auth-btn');
  if (openBtn) {
    e.preventDefault();
    openAuthModal('login');
    return;
  }

  const logoutBtn = e.target.closest('#logoutBtn');
  if (logoutBtn) {
    e.preventDefault();
    logoutUser(true);
    return;
  }

  const profileBtn = e.target.closest('#sidebarProfileBtn');
  if (profileBtn) {
    e.preventDefault();
    if (state.user) {
      switchView('profile');
    } else {
      openAuthModal('login');
    }
    return;
  }
});

$('#closeAuthModalBtn')?.addEventListener('click', closeAuthModal);
$('#authModal')?.addEventListener('click', (e) => {
  if (e.target === $('#authModal')) closeAuthModal();
});
$('#tabLoginBtn')?.addEventListener('click', () => switchAuthTab('login'));
$('#tabRegisterBtn')?.addEventListener('click', () => switchAuthTab('register'));

// 登入表單提交
$('#loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = $('#loginUsername').value.trim();
  const password = $('#loginPassword').value;
  const errorEl = $('#loginError');
  errorEl.classList.add('hidden');

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || (state.lang === 'en' ? 'Login failed' : '登入失敗'));
    }

    localStorage.setItem('auth_token', data.access_token);
    await fetchCurrentUser();
    closeAuthModal();
    toast(state.lang === 'en' ? `Welcome back, ${data.username}!` : `登入成功！歡迎回來，${data.username}`);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
});

// 註冊表單提交
$('#registerForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = $('#regUsername').value.trim();
  const password = $('#regPassword').value;
  const errorEl = $('#regError');
  const successEl = $('#regSuccess');
  errorEl.classList.add('hidden');
  successEl.classList.add('hidden');

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || (state.lang === 'en' ? 'Registration failed' : '註冊失敗'));
    }

    successEl.textContent = data.message || (state.lang === 'en' ? 'Registered! Awaiting admin approval.' : '註冊成功！請等待管理員核准開通。');
    successEl.classList.remove('hidden');
    $('#regUsername').value = '';
    $('#regPassword').value = '';
    setTimeout(() => {
      switchAuthTab('login');
      if ($('#loginUsername')) $('#loginUsername').value = username;
    }, 2000);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
});

// 首頁 Tab 切換與登入/註冊處理
function switchHomeAuthTab(tab) {
  const isLogin = tab === 'login';
  $('#homeTabLoginBtn')?.classList.toggle('active', isLogin);
  $('#homeTabRegisterBtn')?.classList.toggle('active', !isLogin);
  $('#homeLoginForm')?.classList.toggle('hidden', !isLogin);
  $('#homeRegisterForm')?.classList.toggle('hidden', isLogin);
}

$('#homeTabLoginBtn')?.addEventListener('click', () => switchHomeAuthTab('login'));
$('#homeTabRegisterBtn')?.addEventListener('click', () => switchHomeAuthTab('register'));

$('#homeLoginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = $('#homeLoginUsername')?.value.trim();
  const password = $('#homeLoginPassword')?.value;
  const errorEl = $('#homeLoginError');
  if (errorEl) errorEl.classList.add('hidden');

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || (state.lang === 'en' ? 'Login failed' : '登入失敗'));
    }

    localStorage.setItem('auth_token', data.access_token);
    await fetchCurrentUser();
    toast(state.lang === 'en' ? `Welcome back, ${data.username}!` : `登入成功！歡迎回來，${data.username}`);
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = err.message;
      errorEl.classList.remove('hidden');
    }
  }
});

$('#homeRegisterForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = $('#homeRegUsername')?.value.trim();
  const password = $('#homeRegPassword')?.value;
  const errorEl = $('#homeRegError');
  const successEl = $('#homeRegSuccess');
  if (errorEl) errorEl.classList.add('hidden');
  if (successEl) successEl.classList.add('hidden');

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || (state.lang === 'en' ? 'Registration failed' : '註冊失敗'));
    }

    if (successEl) {
      successEl.textContent = data.message || (state.lang === 'en' ? 'Registered! Awaiting admin approval.' : '註冊成功！請等待管理員核准開通。');
      successEl.classList.remove('hidden');
    }
    if ($('#homeRegUsername')) $('#homeRegUsername').value = '';
    if ($('#homeRegPassword')) $('#homeRegPassword').value = '';
    setTimeout(() => {
      switchHomeAuthTab('login');
      if ($('#homeLoginUsername')) $('#homeLoginUsername').value = username;
    }, 2000);
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = err.message;
      errorEl.classList.remove('hidden');
    }
  }
});

// --- 教材處理與核心邏輯 ---

function saveWorkspaceStateToStorage() {
  try {
    const payload = {
      document: state.document,
      deck: state.deck,
      handout: state.handout,
      quiz: state.quiz,
      activeSlide: state.activeSlide || 0,
    };
    localStorage.setItem('lessonflow_workspace_cache', JSON.stringify(payload));
  } catch (err) {
    console.warn('Failed to save state to localStorage:', err);
  }
}

function clearWorkspaceStateStorage() {
  try {
    localStorage.removeItem('lessonflow_workspace_cache');
  } catch (err) {
    console.warn('Failed to clear state from localStorage:', err);
  }
}

function loadWorkspaceStateFromStorage() {
  try {
    const raw = localStorage.getItem('lessonflow_workspace_cache');
    if (!raw) return;
    const payload = JSON.parse(raw);
    if (payload.document) {
      setDocument(payload.document, true);
    }
    if (payload.deck) {
      state.deck = payload.deck;
      state.activeSlide = payload.activeSlide || 0;
      updateModuleStatusChip('deckStatusChip', 'done', state.lang === 'en' ? '✓ Deck Generated' : '✓ 簡報已生成', () => {
        switchView('deck');
        switchPreviewTab('deck');
      });
    }
    if (payload.handout) {
      state.handout = payload.handout;
      updateModuleStatusChip('handoutStatusChip', 'done', state.lang === 'en' ? '✓ Handout Generated' : '✓ 講義已生成', () => {
        switchView('deck');
        switchPreviewTab('handout');
      });
    }
    if (payload.quiz) {
      state.quiz = payload.quiz;
      updateModuleStatusChip('quizStatusChip', 'done', state.lang === 'en' ? '✓ Quiz Sheet Generated' : '✓ 試卷已生成', () => {
        switchView('deck');
        switchPreviewTab('quiz');
      });
    }
    updatePreviewCountBadge();
    renderPreviewPanels();
  } catch (err) {
    console.warn('Failed to load state from localStorage:', err);
  }
}

function setDocument(doc, silent = false) {
  state.document = doc;
  $('#settingsPanel').classList.remove('locked');
  $('#fileCard').classList.remove('hidden');
  $('#fileParsedStatusRow')?.classList.remove('hidden');
  $('#generateBtn').disabled = false;
  if ($('#generateHandoutBtn')) $('#generateHandoutBtn').disabled = false;
  if ($('#generateQuizBtn')) $('#generateQuizBtn').disabled = false;
  if ($('#generateAllBtn')) $('#generateAllBtn').disabled = false;
  $('#settingStatus').textContent = state.lang === 'en' ? '✓ Parsed' : '✓ 已完成解析';
  $('#fileName').textContent = doc.name;
  $('#fileName').title = doc.name;
  $('#fileMeta').textContent = state.lang === 'en'
    ? `${doc.pages} p · ${(doc.size_bytes / 1024 / 1024).toFixed(1)} MB · ${doc.chunks} chunks`
    : `${doc.pages} 頁 · ${(doc.size_bytes / 1024 / 1024).toFixed(1)} MB · ${doc.chunks} 個片段`;
  $('#questionInput').disabled = false;
  $('#sendBtn').disabled = false;
  $('#chatDoc').innerHTML = state.lang === 'en'
    ? `<span>PDF</span><div><b>${escapeHtml(doc.name)}</b><small>${doc.pages} pages · Indexed</small></div>`
    : `<span>PDF</span><div><b>${escapeHtml(doc.name)}</b><small>${doc.pages} 頁 · 已建立索引</small></div>`;
  $('#modeText').textContent = doc.provider_label || '';
  const steps = $$('.step');
  if (steps.length >= 2) {
    steps[0].classList.add('done');
    steps[1].classList.add('active');
  }
  if (!silent) toast(t('toast.pdf_uploaded'));
  saveWorkspaceStateToStorage();
}

async function uploadFile(file) {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in to upload documents' : '請先登入帳號以使用文件上傳功能', true);
    openAuthModal('login');
    return;
  }
  if (!file || (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf')) return toast(t('toast.pdf_invalid'), true);
  const data = new FormData();
  data.append('file', file);
  const enableMultimodal = $('#multimodalToggle') ? $('#multimodalToggle').checked : false;
  data.append('enable_multimodal', enableMultimodal);
  const copyKey = enableMultimodal ? 'loading.read_multimodal_copy' : 'loading.read_fast_copy';
  loading(true, t('loading.read_title'), t(copyKey));
  try { setDocument(await api('/api/documents', { method: 'POST', body: data })); }
  catch (e) { toast(e.message, true); }
  finally { loading(false); }
}

$('#fileInput').addEventListener('change', e => uploadFile(e.target.files[0]));
const dz = $('#dropzone');
['dragenter', 'dragover'].forEach(name => dz.addEventListener(name, e => { e.preventDefault(); dz.classList.add('dragging'); }));
['dragleave', 'drop'].forEach(name => dz.addEventListener(name, e => { e.preventDefault(); dz.classList.remove('dragging'); }));
dz.addEventListener('drop', e => uploadFile(e.dataTransfer.files[0]));
$('#removeFile').addEventListener('click', () => {
  state.document = null;
  $('#settingsPanel').classList.add('locked');
  $('#fileCard').classList.add('hidden');
  $('#fileParsedStatusRow')?.classList.add('hidden');
  $('#generateBtn').disabled = true;
  if ($('#generateHandoutBtn')) $('#generateHandoutBtn').disabled = true;
  if ($('#generateQuizBtn')) $('#generateQuizBtn').disabled = true;
  if ($('#generateAllBtn')) $('#generateAllBtn').disabled = true;
  $('#questionInput').disabled = true;
  $('#sendBtn').disabled = true;
  $('#settingStatus').textContent = t('settings.status_wait');
  ['deckStatusChip', 'handoutStatusChip', 'quizStatusChip'].forEach(id => {
    const el = $(`#${id}`);
    if (el) { el.className = 'module-status-chip'; el.innerHTML = ''; }
  });
  state.deck = null;
  state.handout = null;
  state.quiz = null;
  clearWorkspaceStateStorage();
  updatePreviewCountBadge();
  renderPreviewPanels();
  $$('.step').forEach((s, i) => { if (i) s.classList.remove('active', 'done'); });
  toast(state.lang === 'en' ? 'Removed material from workspace' : '已從工作台移除教材');
});

function toggleTopbar(collapse) {
  const topbar = $('#mainTopbar');
  const restoreBtn = $('#topbarRestoreBtn');
  if (!topbar || !restoreBtn) return;

  const willCollapse = collapse !== undefined ? collapse : !topbar.classList.contains('collapsed');
  if (willCollapse) {
    topbar.classList.add('collapsed');
    restoreBtn.classList.remove('hidden');
    localStorage.setItem('lessonflow_topbar_collapsed', 'true');
  } else {
    topbar.classList.remove('collapsed');
    restoreBtn.classList.add('hidden');
    localStorage.removeItem('lessonflow_topbar_collapsed');
  }
}

$('#topbarCollapseBtn')?.addEventListener('click', () => toggleTopbar(true));
$('#topbarRestoreBtn')?.addEventListener('click', () => toggleTopbar(false));

if (localStorage.getItem('lessonflow_topbar_collapsed') === 'true') {
  toggleTopbar(true);
}

function switchView(name) {
  if (name === 'admin' && (!state.user || state.user.role !== 'admin')) {
    toast(state.lang === 'en' ? 'Admin access only' : '僅限管理員存取控制台', true);
    return;
  }
  if (name === 'profile' && !state.user) {
    toast(state.lang === 'en' ? 'Please log in first' : '請先登入帳號', true);
    openAuthModal('login');
    return;
  }
  $$('.view').forEach(v => v.classList.remove('active'));
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === name));
  if ($(`#${name}View`)) $(`#${name}View`).classList.add('active');

  const crumbs = {
    'home': t('nav.crumb_home'),
    'workspace': t('nav.crumb_workspace'),
    'deck': t('nav.crumb_deck'),
    'chat': t('nav.crumb_chat'),
    'profile': t('nav.crumb_profile'),
    'agent': t('nav.crumb_agent'),
    'admin': t('nav.crumb_admin')
  };
  const subtitles = {
    'home': t('nav.sub_home'),
    'workspace': t('nav.sub_workspace'),
    'deck': t('nav.sub_deck'),
    'chat': t('nav.sub_chat'),
    'profile': t('nav.sub_profile'),
    'agent': t('nav.sub_agent'),
    'admin': t('nav.sub_admin')
  };
  if ($('#crumb')) $('#crumb').textContent = crumbs[name] || t('nav.crumb_home');
  if ($('#crumbSubtitle')) $('#crumbSubtitle').textContent = subtitles[name] ? ` · ${subtitles[name]}` : '';
  if (innerWidth < 950) toggleSidebar(false);


  if (name === 'admin') {
    fetchAllUsers();
  } else if (name === 'profile') {
    renderProfileView();
  } else if (name === 'deck') {
    renderPreviewPanels();
  }
}

function renderProfileView() {
  if (!state.user) return;
  if ($('#profileUsernameText')) $('#profileUsernameText').textContent = state.user.username;
  if ($('#profileRoleText')) $('#profileRoleText').textContent = state.user.role === 'admin' ? t('profile.role_admin') : t('profile.role_user');
  if ($('#profileRoleBadge')) {
    $('#profileRoleBadge').textContent = state.user.role === 'admin' ? t('quota.admin') : t('profile.role_user');
    $('#profileRoleBadge').className = `role-chip ${state.user.role}`;
  }
  if ($('#profileToolbarUserBadge')) {
    $('#profileToolbarUserBadge').textContent = `👤 ${state.user.username || t('profile.top_badge')}`;
  }
  if ($('#profileToolbarRoleText')) {
    $('#profileToolbarRoleText').textContent = state.user.role === 'admin' ? t('quota.admin') : t('profile.role_user');
  }
  if ($('#profileQuotaText') || $('#profileToolbarQuota')) {
    const credits = state.user.credits || {};
    const isUnlimited = state.user.role === 'admin' || credits.is_unlimited;
    if (isUnlimited) {
      if ($('#profileQuotaText')) $('#profileQuotaText').textContent = state.lang === 'en' ? '👑 Admin: Unlimited Credits' : '👑 管理員：無限點數';
      if ($('#profileToolbarQuota')) $('#profileToolbarQuota').textContent = state.lang === 'en' ? '⚡ Admin: Unlimited' : '⚡ 額度：無限配額';
    } else {
      const rem = credits.remaining !== undefined ? credits.remaining : 100;
      const lim = credits.daily_limit || 100;
      const used = credits.used || 0;
      if ($('#profileQuotaText')) {
        $('#profileQuotaText').textContent = state.lang === 'en'
          ? `Remaining: ${rem} / ${lim} pts (Used: ${used} pts)`
          : `今日剩餘點數：${rem} / ${lim} 點 (已用：${used} 點)`;
      }
      if ($('#profileToolbarQuota')) {
        $('#profileToolbarQuota').textContent = state.lang === 'en'
          ? `⚡ Quota: ${rem} / ${lim}`
          : `⚡ 今日額度：${rem} / ${lim} 點`;
      }
    }
  }
}
$$('.nav-item').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.view)));

document.addEventListener('click', (e) => {
  const target = e.target.closest('[data-view]');
  if (target) {
    const viewName = target.dataset.view;
    if (viewName) {
      if (target.tagName === 'A' || target.getAttribute('href') === '#') {
        e.preventDefault();
      }
      switchView(viewName);
      if (target.dataset.previewTab && typeof switchPreviewTab === 'function') {
        switchPreviewTab(target.dataset.previewTab);
      }
    }
  }
});

function toggleSidebar(forceState) {
  const sidebar = $('.sidebar');
  const overlay = $('#sidebarOverlay');
  if (!sidebar) return;
  const isOpen = typeof forceState === 'boolean' ? forceState : !sidebar.classList.contains('open');
  sidebar.classList.toggle('open', isOpen);
  if (overlay) overlay.classList.toggle('active', isOpen);
}

if ($('.menu-toggle')) {
  $('.menu-toggle').addEventListener('click', () => toggleSidebar());
}
if ($('#sidebarOverlay')) {
  $('#sidebarOverlay').addEventListener('click', () => toggleSidebar(false));
}

function renderDeck() {
  const d = state.deck;
  if (!d) {
    if ($('#deckEmptyState')) $('#deckEmptyState').classList.remove('hidden');
    if ($('#deckLayout')) $('#deckLayout').classList.add('hidden');
    if ($('#pptDownload')) $('#pptDownload').classList.add('disabled');
    if ($('#deckPrintSlidesBtn')) $('#deckPrintSlidesBtn').classList.add('disabled');
    if ($('#deckPrintHandoutBtn')) $('#deckPrintHandoutBtn').classList.add('disabled');
    if ($('#deckDownloadDocxBtn')) $('#deckDownloadDocxBtn').classList.add('disabled');
    return;
  }
  if ($('#deckEmptyState')) $('#deckEmptyState').classList.add('hidden');
  if ($('#deckLayout')) $('#deckLayout').classList.remove('hidden');

  const modeLabels = {
    'gemini': state.lang === 'en' ? 'Gemini Cloud' : 'Gemini 雲端生成',
    'openai': state.lang === 'en' ? 'OpenAI Cloud' : 'OpenAI 雲端生成',
    'ollama_cloud': state.lang === 'en' ? 'Ollama Cloud' : 'Ollama 雲端生成',
    'ollama_local': state.lang === 'en' ? 'Ollama Local' : 'Ollama 本機生成',
    'ollama': state.lang === 'en' ? 'Ollama Local' : 'Ollama 本機生成',
  };
  const modeText = modeLabels[d.mode] || (state.lang === 'en' ? 'AI Generated' : 'AI 生成');
  const slideText = state.lang === 'en' ? `${d.slides.length} Slides` : `${d.slides.length} 張投影片`;
  if ($('#deckTitle')) $('#deckTitle').textContent = d.title;
  if ($('#deckSubtitle')) $('#deckSubtitle').textContent = `${d.subtitle} · ${slideText} · ${modeText}`;
  if ($('#pptDownload')) {
    $('#pptDownload').href = `/api/decks/${d.id}/pptx`;
    $('#pptDownload').classList.remove('disabled');
  }
  if ($('#deckPrintSlidesBtn')) {
    $('#deckPrintSlidesBtn').href = `/api/decks/${d.id}/pdf`;
    $('#deckPrintSlidesBtn').classList.remove('disabled');
  }
  if ($('#deckPrintHandoutBtn')) {
    $('#deckPrintHandoutBtn').href = `/api/decks/${d.id}/handout/print`;
    $('#deckPrintHandoutBtn').classList.remove('disabled');
  }
  if ($('#deckDownloadDocxBtn')) {
    $('#deckDownloadDocxBtn').href = `/api/decks/${d.id}/docx`;
    $('#deckDownloadDocxBtn').classList.remove('disabled');
  }
  if ($('#slideList')) {
    $('#slideList').innerHTML = d.slides.map((s, i) => `<div class="slide-thumb ${i === 0 ? 'active' : ''}" data-index="${i}"><small>${String(i + 1).padStart(2, '0')}</small><div class="mini-slide"><b>${formatMarkdown(s.title)}</b>${s.bullets.slice(0, 3).map(() => '<i></i>').join('')}</div></div>`).join('');
    $$('.slide-thumb').forEach(t => t.addEventListener('click', () => showSlide(+t.dataset.index)));
  }
  showSlide(0);
}

const katexOptions = {
  delimiters: [
    { left: '$$', right: '$$', display: true },
    { left: '$', right: '$', display: false },
    { left: '\\(', right: '\\)', display: false },
    { left: '\\[', right: '\\]', display: true }
  ],
  throwOnError: false
};

function unescapeMathInElement(element) {
  if (!element) return;
  let html = element.innerHTML;
  html = html.replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, (match) => {
    return match
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
  });
  element.innerHTML = html;
}

function renderMath(element) {
  if (typeof renderMathInElement === 'function' && element) {
    try {
      unescapeMathInElement(element);
      renderMathInElement(element, katexOptions);
    } catch (e) {
      console.warn('KaTeX render error:', e);
    }
  }
}

function renderMarkdownToHtml(mdText) {
  if (!mdText) return '';

  // 1. Stash Math blocks so Markdown parser does not corrupt math syntax
  const mathPlaceholders = [];
  let processed = String(mdText).replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, (match) => {
    const placeholder = `%%MATHBLOCK${mathPlaceholders.length}%%`;
    mathPlaceholders.push(match);
    return placeholder;
  });

  // 2. Stash Code blocks (```lang ... ```)
  const codePlaceholders = [];
  processed = processed.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `%%CODEBLOCK${codePlaceholders.length}%%`;
    codePlaceholders.push({ lang: lang.trim(), code: code.trim() });
    return placeholder;
  });

  // 3. Normalize CRLF
  processed = processed.replace(/\r\n/g, '\n');

  // 4. Headers (#, ##, ###, ####, #####, ######)
  processed = processed.replace(/^######\s+(.*)$/gm, '<h6>$1</h6>');
  processed = processed.replace(/^#####\s+(.*)$/gm, '<h5>$1</h5>');
  processed = processed.replace(/^####\s+(.*)$/gm, '<h4>$1</h4>');
  processed = processed.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
  processed = processed.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
  processed = processed.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');

  // 5. Horizontal rules
  processed = processed.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr>');

  // 6. Blockquotes
  processed = processed.replace(/^>\s+(.*)$/gm, '<blockquote>$1</blockquote>');
  processed = processed.replace(/<\/blockquote>\n<blockquote>/g, '<br>');

  // 7. Inline styling (code, bold, italic)
  processed = processed.replace(/`([^`\n]+)`/g, '<code class="agent-inline-code">$1</code>');
  processed = processed.replace(/\*\*([^\*\n]+)\*\*/g, '<strong>$1</strong>');
  processed = processed.replace(/__([^_\n]+)__/g, '<strong>$1</strong>');
  processed = processed.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
  processed = processed.replace(/_([^_\n]+)_/g, '<em>$1</em>');

  // 8. Lists
  processed = processed.replace(/^[\*\-\+]\s+(.*)$/gm, '<li>$1</li>');
  processed = processed.replace(/^\d+\.\s+(.*)$/gm, '<li class="agent-ol-item">$1</li>');

  processed = processed.replace(/(<li class="agent-ol-item">[\s\S]*?<\/li>(\n|$))+/g, match => {
    return `<ol class="agent-ol">${match.replace(/ class="agent-ol-item"/g, '')}</ol>`;
  });
  processed = processed.replace(/(<li>[\s\S]*?<\/li>(\n|$))+/g, '<ul class="agent-ul">$&</ul>');

  // 9. Tables
  processed = processed.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (tableBlock) => {
    const rows = tableBlock.trim().split('\n').map(r => r.trim()).filter(Boolean);
    if (rows.length >= 2 && rows.some(r => /\|[\s\-:]+\|\s*/.test(r))) {
      let html = '<div class="agent-table-wrapper"><table class="agent-table">';
      let isHeader = true;
      for (const row of rows) {
        if (/^\|[\s\-:|]+\|$/.test(row)) {
          isHeader = false;
          continue;
        }
        const cells = row.split('|').slice(1, -1).map(c => c.trim());
        if (cells.length === 0) continue;
        html += '<tr>';
        const tag = isHeader ? 'th' : 'td';
        for (const cell of cells) {
          html += `<${tag}>${cell}</${tag}>`;
        }
        html += '</tr>';
      }
      html += '</table></div>';
      return html;
    }
    return tableBlock;
  });

  // 10. Paragraphs
  const blocks = processed.split(/\n{2,}/);
  processed = blocks.map(block => {
    block = block.trim();
    if (!block) return '';
    if (/^<(h[1-6]|ul|ol|table|div|blockquote|hr|pre)/.test(block)) {
      return block;
    }
    return `<p class="agent-p">${block.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  // 11. Restore Code blocks
  codePlaceholders.forEach((item, idx) => {
    const escaped = escapeHtml(item.code);
    const langLabel = escapeHtml(item.lang || 'code');
    const codeHtml = `<pre class="agent-code-block"><div class="agent-code-header"><span>${langLabel}</span><button type="button" class="agent-code-copy-btn" onclick="navigator.clipboard.writeText(this.closest('.agent-code-block').querySelector('code').innerText); toast('已複製代碼');">複製</button></div><code>${escaped}</code></pre>`;
    processed = processed.replace(`%%CODEBLOCK${idx}%%`, codeHtml);
  });

  // 12. Restore Math tokens
  mathPlaceholders.forEach((math, idx) => {
    processed = processed.replace(`%%MATHBLOCK${idx}%%`, math);
  });

  return processed;
}


function extractEmoji(str) {
  if (!str) return '💡';
  const match = str.match(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B50}]/u);
  if (match) return match[0];
  const clean = str.toLowerCase().trim();
  if (clean.includes('bulb') || clean.includes('idea')) return '💡';
  if (clean.includes('book') || clean.includes('text')) return '📚';
  if (clean.includes('chart') || clean.includes('graph')) return '📊';
  if (clean.includes('gear') || clean.includes('process')) return '⚙️';
  if (clean.includes('brain') || clean.includes('think')) return '🧠';
  if (clean.includes('lightning') || clean.includes('power')) return '⚡';
  if (clean.includes('lock')) return '🔒';
  if (clean.includes('globe') || clean.includes('web')) return '🌐';
  if (clean.includes('target') || clean.includes('goal')) return '🎯';
  if (clean.includes('microscope') || clean.includes('science')) return '🔬';
  if (clean.includes('search')) return '🔍';
  return '💡';
}

function formatMarkdown(text) {
  if (!text) return '';
  const mathPlaceholders = [];
  let processed = String(text).replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, (match) => {
    const placeholder = `%%MATHBLOCK${mathPlaceholders.length}%%`;
    mathPlaceholders.push(match);
    return placeholder;
  });
  processed = escapeHtml(processed);
  processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  processed = processed.replace(/__([^_]+?)__/g, '<strong>$1</strong>');
  processed = processed.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g, '<em>$1</em>');
  processed = processed.replace(/`([^`\n]+?)`/g, '<code>$1</code>');
  mathPlaceholders.forEach((math, idx) => {
    processed = processed.replace(`%%MATHBLOCK${idx}%%`, math);
  });
  return processed;
}

function renderVisualDiagramCard(slide, index) {
  const visDiagram = slide.visual_diagram || {};
  const diagramType = visDiagram.diagram_type || 'flowchart';
  const typeTitles = {
    flowchart: '🔄 機制流程推導',
    comparison: '⚖️ 核心概念對比',
    key_formula: '🧮 關鍵公式解析',
    concept_map: '📐 觀念架構圖解',
  };
  const headerText = typeTitles[diagramType] || '📐 觀念圖解與推導';

  let rawSteps = visDiagram.steps;
  let diagramSteps = [];
  if (Array.isArray(rawSteps) && rawSteps.length > 0) {
    diagramSteps = rawSteps.map((s, sIdx) => {
      if (typeof s === 'object' && s !== null) {
        return { label: s.label || `觀念重點 ${sIdx + 1}`, text: s.text || '' };
      }
      return { label: `觀念重點 ${sIdx + 1}`, text: String(s) };
    });
  } else {
    diagramSteps = [
      { label: '① 核心機制', text: `聚焦【${slide.title || '本單元'}】之根本原理與邏輯架構` },
      { label: '② 推導關鍵', text: slide.visual_description ? slide.visual_description.slice(0, 60) : '依據教材推導並掌握概念關鍵特徵' }
    ];
  }

  const takeawayText = visDiagram.takeaway || slide.visual_description || '深入掌握本單元核心機制與概念推導。';

  const stepsHtml = diagramSteps.slice(0, 3).map((step, idx) => `
    <div class="visual-step-box step-idx-${idx}">
      <div class="visual-step-label">${formatMarkdown(step.label)}</div>
      <div class="visual-step-text" contenteditable="true" spellcheck="false" data-step-idx="${idx}" title="點擊可直接修改步驟說明">${formatMarkdown(step.text)}</div>
    </div>
  `).join('');

  return `
    <div class="visual-card">
      <div class="visual-card-head">
        <span>${escapeHtml(headerText)}</span>
      </div>
      <div class="visual-card-steps">
        ${stepsHtml}
      </div>
      <div class="visual-card-takeaway">
        <div class="visual-takeaway-head">💡 核心結論與關鍵理解：</div>
        <div class="visual-takeaway-text" contenteditable="true" spellcheck="false" title="點擊可直接修改核心結論">${formatMarkdown(takeawayText)}</div>
      </div>
    </div>
  `;
}

function updateGlobalSyncStatus(status) {
  const el = $('#globalEditSyncIndicator');
  if (!el) return;
  if (status === 'saving') {
    el.textContent = '⏳ 儲存中...';
    el.className = 'edit-sync-indicator saving';
  } else if (status === 'saved') {
    el.textContent = '✓ 已同步儲存';
    el.className = 'edit-sync-indicator saved';
  } else {
    el.textContent = '✓ 隨時自動同步';
    el.className = 'edit-sync-indicator';
  }
}

let patchDeckTimeout = null;
function syncDeckEdits(showToast = false) {
  if (!state.deck) return;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  clearTimeout(patchDeckTimeout);
  patchDeckTimeout = setTimeout(async () => {
    try {
      await api(`/api/decks/${state.deck.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: state.deck.title,
          subtitle: state.deck.subtitle,
          slides: state.deck.slides
        })
      });
      updateGlobalSyncStatus('saved');
      if (showToast) toast('簡報修改內容已同步');
    } catch (err) {
      updateGlobalSyncStatus('saved');
    }
  }, 500);
}

async function flushDeckEdits() {
  if (!state.deck) return;
  clearTimeout(patchDeckTimeout);
  patchDeckTimeout = null;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  try {
    await api(`/api/decks/${state.deck.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: state.deck.title,
        subtitle: state.deck.subtitle,
        slides: state.deck.slides
      })
    });
    updateGlobalSyncStatus('saved');
  } catch (err) {
    console.warn('Flush deck edits warning:', err);
    updateGlobalSyncStatus('saved');
  }
}

async function refineActiveSlideNotes() {
  if (!state.deck || state.activeSlide === undefined) return;
  const btn = $('#refineNotesBtn');
  const spinner = btn ? btn.querySelector('.btn-inline-spinner') : null;
  const lbl = btn ? btn.querySelector('.btn-lbl') : null;
  const slideIndex = state.activeSlide;

  if (btn) btn.disabled = true;
  if (spinner) spinner.classList.remove('hidden');
  if (lbl) lbl.textContent = '✨ AI 潤飾中...';

  try {
    const res = await api(`/api/decks/${state.deck.id}/slides/${slideIndex}/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction: '潤飾講稿與要點，使口語表達更自然、生動且具啟發性' })
    });
    if (res && res.slide) {
      state.deck.slides[slideIndex] = res.slide;
      showSlide(slideIndex);
      toast('✨ 投影片講稿潤飾完成！(消耗 3 點)');
      await fetchCurrentUser();
    }
  } catch (err) {
    toast(err.message || '講稿潤飾失敗', true);
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.classList.add('hidden');
    if (lbl) lbl.textContent = '✨ AI 講稿潤飾 (3 點)';
  }
}

$('#refineNotesBtn')?.addEventListener('click', () => refineActiveSlideNotes());

function showSlide(index) {
  state.activeSlide = index;
  const s = state.deck.slides[index];
  if (!s) return;
  $$('.slide-thumb').forEach((t, i) => t.classList.toggle('active', i === index));
  $('#slideStage').dataset.page = String(index + 1).padStart(2, '0');

  const iconStr = extractEmoji(s.icon);
  const visualCardHtml = `
    <div class="visual-diagram-container">
      ${renderVisualDiagramCard(s, index)}
    </div>
  `;

  $('#slideStage').innerHTML = `
    <div class="slide-header-wrap">
      <h2><span class="slide-title-icon">${escapeHtml(iconStr)}</span> <span class="slide-title-editable" contenteditable="true" spellcheck="false" title="點擊可直接修改投影片標題">${formatMarkdown(s.title)}</span></h2>
    </div>
    <div class="slide-content-grid has-visual">
      <div class="slide-bullets-wrap">
        <ul>${s.bullets.map((b, bIdx) => `<li contenteditable="true" spellcheck="false" data-bullet-idx="${bIdx}" title="點擊可直接修改要點">${formatMarkdown(b)}</li>`).join('')}</ul>
      </div>
      ${visualCardHtml}
    </div>
  `;

  const notesEl = $('#speakerNotes');
  if (notesEl) {
    notesEl.textContent = s.speaker_notes || '';
  }

  renderMath($('#slideStage'));
  renderMath($('#speakerNotes'));
  if (s.source_pages && s.source_pages.length) {
    $('#pageRef').textContent = state.lang === 'en' ? `Page ${s.source_pages.join(', ')}` : `教材第 ${s.source_pages.join('、')} 頁`;
  } else {
    $('#pageRef').textContent = t('deck.page_ref');
  }
}

// 容器層事件代理：簡報就地即時編輯
$('#slideStage')?.addEventListener('input', (e) => {
  if (!state.deck || !state.deck.slides || state.activeSlide === undefined) return;
  const slide = state.deck.slides[state.activeSlide];
  if (!slide) return;
  const target = e.target;

  // 1. 投影片標題
  const titleEl = target.closest('.slide-title-editable');
  if (titleEl) {
    slide.title = titleEl.innerText.trim();
    const thumbB = $(`.slide-thumb[data-index="${state.activeSlide}"] b`);
    if (thumbB) thumbB.textContent = slide.title;
    syncDeckEdits();
    return;
  }

  // 2. 條列要點
  const bulletLi = target.closest('li[data-bullet-idx]');
  if (bulletLi) {
    const bIdx = parseInt(bulletLi.dataset.bulletIdx, 10);
    if (!Array.isArray(slide.bullets)) slide.bullets = [];
    slide.bullets[bIdx] = bulletLi.innerText;
    syncDeckEdits();
    return;
  }

  // 3. 視覺圖解步驟文字
  const stepTextEl = target.closest('.visual-step-text[data-step-idx]');
  if (stepTextEl) {
    const sIdx = parseInt(stepTextEl.dataset.stepIdx, 10);
    if (!slide.visual_diagram) slide.visual_diagram = {};
    if (!Array.isArray(slide.visual_diagram.steps)) {
      slide.visual_diagram.steps = [
        { label: '① 核心機制', text: '' },
        { label: '② 推導關鍵', text: '' }
      ];
    }
    while (slide.visual_diagram.steps.length <= sIdx) {
      slide.visual_diagram.steps.push({ label: `觀念重點 ${slide.visual_diagram.steps.length + 1}`, text: '' });
    }
    if (typeof slide.visual_diagram.steps[sIdx] === 'object' && slide.visual_diagram.steps[sIdx] !== null) {
      slide.visual_diagram.steps[sIdx].text = stepTextEl.innerText;
    } else {
      slide.visual_diagram.steps[sIdx] = { label: `觀念重點 ${sIdx + 1}`, text: stepTextEl.innerText };
    }
    syncDeckEdits();
    return;
  }

  // 4. 視覺圖解核心結論
  const takeawayEl = target.closest('.visual-takeaway-text');
  if (takeawayEl) {
    if (!slide.visual_diagram) slide.visual_diagram = {};
    slide.visual_diagram.takeaway = takeawayEl.innerText;
    syncDeckEdits();
    return;
  }
});

// 容器層事件代理：逐頁講稿即時編輯
$('#speakerNotes')?.addEventListener('input', () => {
  if (!state.deck || !state.deck.slides || state.activeSlide === undefined) return;
  const slide = state.deck.slides[state.activeSlide];
  if (!slide) return;
  slide.speaker_notes = $('#speakerNotes').innerText;
  syncDeckEdits();
});

function addUserMessage(text) {
  const el = document.createElement('div');
  el.className = 'message user';
  el.innerHTML = `<div>${escapeHtml(text)}</div>`;
  $('#messages').append(el);
  scrollMessages();
}

function addAssistantMessage(data, userQuestion = '') {
  const el = document.createElement('div');
  el.className = 'message assistant';
  const isEn = state.lang === 'en';
  const sources = data.sources && data.sources.length
    ? data.sources.slice(0, 3).map(s => `<div class="source"><b>${isEn ? 'Page ' + s.page : '第 ' + s.page + ' 頁'}</b><p>${escapeHtml(s.excerpt)}</p></div>`).join('')
    : '';
  const providerLabel = data.mode === 'gemini' ? 'Gemini' : (data.mode === 'openai' ? 'OpenAI' : (data.mode === 'claude' ? 'Claude' : 'AI'));
  const deptLabel = isEn ? '📖 Material Q&A' : '📖 教材助教';

  // 動態生成智能追問建議標籤
  const followUpChips = isEn ? [
    { label: '🔍 Explain in depth', query: 'Can you explain the key details and underlying principles in greater depth?' },
    { label: '💡 Real-world examples', query: 'Could you provide a concrete real-life example to illustrate this concept?' },
    { label: '📝 Bulleted summary', query: 'Please summarize this explanation into clear bullet points for student revision.' },
    { label: '📑 Create 3 quiz questions', query: 'Based on this topic, generate 3 multiple-choice quiz questions with answer keys.' }
  ] : [
    { label: '🔍 深入說明核心細節', query: '能針對剛才說明的關鍵概念，進一步深入解析其底層原理與細節嗎？' },
    { label: '💡 舉個生活實例', query: '請舉一個生動的生活情境實例，幫助學生更容易理解這個概念。' },
    { label: '📝 整理為條列重點', query: '請將剛才的解答內容，整理為清楚好記的條列式教學重點筆記。' },
    { label: '📑 出 3 題隨堂測驗', query: '請依據這段教學內容，設計 3 題單選測驗題並附上正確答案與解析。' }
  ];

  const followUpHtml = `
    <div class="follow-up-suggestions">
      <div class="follow-up-label">
        <span>⚡</span> <span>${isEn ? 'Suggested Follow-up Questions (Context-Aware):' : '推薦延續追問（結合上下文記憶）：'}</span>
      </div>
      ${followUpChips.map(c => `<button type="button" class="follow-up-chip chat-sug-btn" data-query="${escapeHtml(c.query)}">${escapeHtml(c.label)}</button>`).join('')}
    </div>
  `;

  el.innerHTML = `
    <span class="bot-avatar">✦</span>
    <div>
      <div class="agent-msg-meta">
        <span class="agent-dept-chip">${deptLabel}</span>
        <span class="agent-skill-chip">⚡ ${providerLabel} Self-RAG</span>
      </div>
      <div class="agent-output-content">${renderMarkdownToHtml(data.answer)}</div>
      ${sources ? `<div class="source-list"><span>${isEn ? 'Cited Sources · Page References' : '回答依據 · 教材來源頁碼'}</span>${sources}</div>` : ''}
      ${followUpHtml}
      <div class="agent-action-bar" style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
        <button type="button" class="agent-action-btn agent-copy-btn" data-copy="${escapeHtml(data.answer)}">${isEn ? '📋 Copy Answer' : '📋 複製回答'}</button>
        <button type="button" class="agent-action-btn agent-pptx-btn" data-query="${escapeHtml(userQuestion || '')}" data-copy="${escapeHtml(data.answer)}">${isEn ? '📄 Import to Workspace' : '📄 導入教案工作台'}</button>
      </div>
    </div>
  `;
  $('#messages').append(el);
  scrollMessages();
  renderMath(el);
}

function scrollMessages() { const m = $('#messages'); if (m) m.scrollTop = m.scrollHeight; }
function escapeHtml(value) { const d = document.createElement('div'); d.textContent = value; return d.innerHTML; }

// 開啟新對話 / 清除問答歷史按鈕
$('#clearChatBtn')?.addEventListener('click', () => {
  state.chatHistory = [];
  const messages = $('#messages');
  if (messages) {
    const isEn = state.lang === 'en';
    messages.innerHTML = `
      <div class="message assistant welcome"><span class="bot-avatar">✦</span>
        <div><b data-i18n="chat.welcome_b">${isEn ? '💡 Hi, I am your Teaching Material Assistant' : '💡 嗨，我是你的教材助教'}</b>
          <p data-i18n="chat.welcome_p">${isEn ? 'Upload documents to ask questions, compare concepts, or summarize key takeaways. I answer strictly based on your materials and maintain our conversation context.' : '上傳文件後，你可以請我解釋概念、比較差異，或從教材中整理重點。我只會根據文件內容回答，並記住我們的對話脈絡。'}</p>
          <div class="suggestions">
            <button type="button" class="chat-sug-btn" data-query="${isEn ? 'What are the 3 core takeaways of this material?' : '這份教材的三個核心重點是什麼？'}">${isEn ? '🎓 3 Core Key Takeaways' : '🎓 這份教材的三個核心重點是什麼？'}</button>
            <button type="button" class="chat-sug-btn" data-query="${isEn ? 'Explain the key concepts with real-world examples' : '用簡單的例子解釋最重要的概念'}">${isEn ? '📝 Explain with Simple Examples' : '📝 用簡單的例子解釋最重要的概念'}</button>
          </div>
        </div>
      </div>
    `;
  }
  toast(state.lang === 'en' ? 'Chat history reset. Started a new session.' : '已清空對話紀錄，開啟全新問答！');
});

// === 動態多階段進度流水線 (Dynamic Multi-Stage Pipeline for Self-RAG & Agent) ===
function createStagePipeline(container, stages) {
  if (!container) return { finish: () => {}, destroy: () => {} };
  let currentIndex = 0;
  let intervalId = null;

  function render() {
    container.innerHTML = stages.map((st, idx) => {
      let statusClass = 'pending';
      let indicatorContent = String(idx + 1);
      if (idx < currentIndex) {
        statusClass = 'done';
        indicatorContent = '✓';
      } else if (idx === currentIndex) {
        statusClass = 'active';
        indicatorContent = '●';
      }
      return `
        <div class="stage-step ${statusClass}">
          <span class="stage-indicator">${indicatorContent}</span>
          <span class="stage-text">${escapeHtml(st.text)}</span>
        </div>
      `;
    }).join('');
  }

  render();

  intervalId = setInterval(() => {
    if (currentIndex < stages.length - 1) {
      currentIndex++;
      render();
    }
  }, 1100);

  return {
    finish() {
      if (intervalId) clearInterval(intervalId);
      currentIndex = stages.length;
      render();
    },
    destroy() {
      if (intervalId) clearInterval(intervalId);
    }
  };
}

$('#chatForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  if (!state.user) {
    toast('請先登入帳號以開始問答', true);
    openAuthModal('login');
    return;
  }
  const input = $('#questionInput');
  const question = input.value.trim();
  if (!question || !state.document) return;

  if (!state.chatHistory) state.chatHistory = [];
  state.chatHistory.push({ role: 'user', content: question });

  addUserMessage(question);
  input.value = '';
  $('#sendBtn').disabled = true;

  const enable_web_search = $('#qaWebSearch') ? $('#qaWebSearch').checked : false;
  const isEn = state.lang === 'en';

  const qaStages = isEn ? [
    { text: 'Retrieving document chunks & vector context...' },
    { text: 'AI synthesizing key concepts & structuring explanation...' },
    { text: 'Executing Self-RAG audit · Verifying material grounding & facts...' }
  ] : [
    { text: '正在檢索教材關鍵段落與向量特徵...' },
    { text: 'AI 正在組織教學重點與觀念解析...' },
    { text: '執行 Self-RAG 溯源防幻覺審查 · 核對事實依據...' }
  ];

  const typing = document.createElement('div');
  typing.className = 'message assistant loading-turn';
  typing.innerHTML = `
    <span class="bot-avatar">✦</span>
    <div>
      <div class="agent-msg-meta">
        <span class="agent-dept-chip">${isEn ? '📖 Material Q&A' : '📖 教材助教'}</span>
      </div>
      <div class="stage-pipeline" id="qaStagePipeline"></div>
    </div>
  `;
  $('#messages').append(typing);
  scrollMessages();

  const pipelineContainer = typing.querySelector('#qaStagePipeline');
  const pipeline = createStagePipeline(pipelineContainer, qaStages);

  try {
    const data = await api('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: state.document.id,
        question,
        enable_web_search,
        history: state.chatHistory.slice(-8)
      })
    });
    pipeline.finish();
    await new Promise(r => setTimeout(r, 200));
    typing.remove();

    // 紀錄 Assistant Turn
    state.chatHistory.push({ role: 'assistant', content: data.answer });

    addAssistantMessage(data, question);
    await fetchCurrentUser();
  } catch (err) {
    pipeline.destroy();
    typing.remove();
    toast(err.message, true);
  } finally {
    $('#sendBtn').disabled = false;
  }
});

$('#questionInput')?.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#chatForm')?.requestSubmit(); } });
$$('#chatView .suggestions button, .chat-sug-btn').forEach(btn => btn.addEventListener('click', () => {
  if (!state.document) return toast(state.lang === 'en' ? 'Please upload material first' : '請先上傳教材', true);
  const q = btn.dataset.query || btn.textContent.replace(/^[🎓📝🚀📋💡🔍]\s*/, '').trim();
  if ($('#questionInput')) $('#questionInput').value = q;
  $('#chatForm')?.requestSubmit();
}));
// 簡報匯出按鈕立即 Flush 同步攔截
$('#pptDownload')?.addEventListener('click', async (e) => {
  if (!state.deck) return;
  e.preventDefault();
  await flushDeckEdits();
  toast(state.lang === 'en' ? 'Downloading PowerPoint presentation...' : '正在下載 PowerPoint 簡報');
  window.location.href = `/api/decks/${state.deck.id}/pptx`;
});
$('#deckPrintSlidesBtn')?.addEventListener('click', async (e) => {
  if (!state.deck) return;
  e.preventDefault();
  await flushDeckEdits();
  window.open(`/api/decks/${state.deck.id}/pdf`, '_blank');
});
$('#deckPrintHandoutBtn')?.addEventListener('click', async (e) => {
  if (!state.deck) return;
  e.preventDefault();
  await flushDeckEdits();
  window.open(`/api/decks/${state.deck.id}/handout/print`, '_blank');
});
$('#deckDownloadDocxBtn')?.addEventListener('click', async (e) => {
  if (!state.deck) return;
  e.preventDefault();
  await flushDeckEdits();
  window.location.href = `/api/decks/${state.deck.id}/docx`;
});

// ── AI 提供者 (Provider) 切換與 UI 更新 ──
function updateProviderUI(info) {
  if (!info) return;
  state.provider = info.provider;
  if ($('#providerSelect')) $('#providerSelect').value = info.provider;
  const badges = {
    'gemini': state.lang === 'en' ? 'Gemini Cloud' : 'Gemini 雲端',
    'openai': state.lang === 'en' ? 'OpenAI Cloud' : 'OpenAI 雲端',
    'ollama_cloud': state.lang === 'en' ? 'Ollama Cloud' : 'Ollama 雲端',
    'ollama_local': state.lang === 'en' ? 'Ollama Local' : 'Ollama 本機'
  };
  const providerLabels = {
    'gemini': state.lang === 'en' ? 'Gemini Cloud' : 'Gemini 雲端',
    'openai': state.lang === 'en' ? 'OpenAI Cloud' : 'OpenAI 雲端',
    'ollama_cloud': state.lang === 'en' ? 'Ollama Cloud' : 'Ollama 雲端',
    'ollama_local': state.lang === 'en' ? 'Ollama Local' : 'Ollama 本機'
  };
  if ($('#providerBadge')) $('#providerBadge').textContent = badges[info.provider] || 'Gemini';
  if ($('#modeText')) $('#modeText').textContent = providerLabels[info.provider] || info.provider_label || badges[info.provider] || (state.lang === 'en' ? 'AI Ready' : 'AI 就緒');
}

// 頁面加載時拉取當前服務資訊與登入狀態
fetch('/api/health')
  .then(r => r.json())
  .then(x => updateProviderUI(x))
  .catch(() => { if ($('#modeText')) $('#modeText').textContent = state.lang === 'en' ? 'Disconnected' : '服務未連線'; });

$('#providerSelect')?.addEventListener('change', async (e) => {
  const newProvider = e.target.value;
  const oldProvider = state.provider;
  try {
    const data = await api('/api/provider', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: newProvider })
    });
    updateProviderUI(data);
    const labelKey = `opt.provider.${data.provider || newProvider}`;
    const label = t(labelKey) || newProvider;
    toast(state.lang === 'en' ? `Switched AI provider to: ${label}` : `已切換 AI 模型提供者為：${label}`);
  } catch (err) {
    if ($('#providerSelect')) $('#providerSelect').value = oldProvider;
    toast(err.message, true);
  }
});

fetchCurrentUser();
loadWorkspaceStateFromStorage();



// === 管理員控制台 (Admin Modal) 與 個人設定 (Profile Modal) 邏輯 ===

function updateAdminUI() {
  const isAdmin = !!(state.user && state.user.role === 'admin');
  $$('.admin-only').forEach(el => {
    if (isAdmin) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });

  if (isAdmin) {
    fetchPendingCount();
  } else {
    closeAdminModal();
    const adminView = $('#adminView');
    if (adminView && adminView.classList.contains('active')) {
      switchView('workspace');
    }
  }
}

async function fetchPendingCount() {
  try {
    const data = await api('/api/admin/users/pending');
    const count = data.pending_users ? data.pending_users.length : 0;
    if ($('#pendingBadge')) $('#pendingBadge').textContent = count;
    if ($('#pendingTabCount')) $('#pendingTabCount').textContent = count;
  } catch (e) {
    // 靜默處理
  }
}

function openAdminModal(tab = 'pending') {
  if (!state.user || state.user.role !== 'admin') {
    toast('僅限管理員存取', true);
    return;
  }
  switchAdminTab(tab);
  const modal = $('#adminModal');
  if (modal) modal.classList.remove('hidden');
}

function closeAdminModal() {
  const modal = $('#adminModal');
  if (modal) modal.classList.add('hidden');
}

function switchAdminTab(tab) {
  const isPending = tab === 'pending';
  if ($('#tabPendingUsersBtn')) $('#tabPendingUsersBtn').classList.toggle('active', isPending);
  if ($('#tabAllUsersBtn')) $('#tabAllUsersBtn').classList.toggle('active', !isPending);
  if ($('#pendingUsersTab')) $('#pendingUsersTab').classList.toggle('hidden', !isPending);
  if ($('#allUsersTab')) $('#allUsersTab').classList.toggle('hidden', isPending);

  if (isPending) {
    fetchPendingUsers();
  } else {
    fetchAllUsers();
  }
}

async function fetchPendingUsers() {
  const tbody = $('#pendingUsersTbody');
  if (!tbody) return;
  const isEn = state.lang === 'en';
  tbody.innerHTML = `<tr><td colspan="4" class="text-center muted">${isEn ? 'Loading...' : '載入中…'}</td></tr>`;

  try {
    const data = await api('/api/admin/users/pending');
    const users = data.pending_users || [];
    fetchPendingCount();

    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center muted">${isEn ? 'No pending account registrations' : '尚無待審核之帳號'}</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td><b>${escapeHtml(u.username)}</b></td>
        <td><span class="role-chip ${u.role}">${u.role === 'admin' ? (isEn ? 'Admin' : '管理員') : (isEn ? 'User' : '一般用戶')}</span></td>
        <td>${escapeHtml(u.created_at || (isEn ? 'Recent' : '最近'))}</td>
        <td>
          <button class="btn-sm btn-approve" data-review="approve" data-user="${escapeHtml(u.username)}">${isEn ? '✓ Approve' : '✓ 核准'}</button>
          <button class="btn-sm btn-reject" data-review="reject" data-user="${escapeHtml(u.username)}">${isEn ? '✗ Reject' : '✗ 拒絕'}</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">${isEn ? 'Load failed' : '載入失敗'}: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function formatLastLoginTime(timestamp) {
  if (!timestamp) return state.lang === 'en' ? 'Never' : '尚未上記錄';
  try {
    const d = new Date(timestamp.replace(' ', 'T') + 'Z');
    if (isNaN(d.getTime())) return timestamp;
    const now = new Date();
    const diffSec = Math.floor((now - d) / 1000);
    if (diffSec < 60) return state.lang === 'en' ? 'Just now' : '剛剛';
    if (diffSec < 3600) {
      const mins = Math.floor(diffSec / 60);
      return state.lang === 'en' ? `${mins}m ago` : `${mins} 分鐘前`;
    }
    if (diffSec < 86400) {
      const hours = Math.floor(diffSec / 3600);
      return state.lang === 'en' ? `${hours}h ago` : `${hours} 小時前`;
    }
    return timestamp.slice(0, 16);
  } catch (e) {
    return timestamp;
  }
}

async function fetchAllUsers() {
  const tbody = $('#allUsersTbody');
  const cardsWrapper = $('#allUsersCards');
  if (!tbody) return;
  const isEn = state.lang === 'en';
  tbody.innerHTML = `<tr><td colspan="8" class="text-center muted">${isEn ? 'Loading...' : '載入中…'}</td></tr>`;
  if (cardsWrapper) cardsWrapper.innerHTML = `<div class="text-center muted">${isEn ? 'Loading...' : '載入中…'}</div>`;

  try {
    const data = await api('/api/admin/users/list');
    let users = data.users || [];

    // 依據「管理員優先」+「上次上線時間 (新到舊)」進行排序
    users.sort((a, b) => {
      if (a.role === 'admin' && b.role !== 'admin') return -1;
      if (a.role !== 'admin' && b.role === 'admin') return 1;

      const timeA = a.last_login_at ? new Date(a.last_login_at.replace(' ', 'T') + 'Z').getTime() : 0;
      const timeB = b.last_login_at ? new Date(b.last_login_at.replace(' ', 'T') + 'Z').getTime() : 0;
      if (timeA !== timeB) return timeB - timeA;

      return a.id - b.id;
    });

    const total = users.length;
    const pending = users.filter(u => u.status === 'pending').length;
    const admins = users.filter(u => u.role === 'admin').length;
    if ($('#metricTotalUsers')) $('#metricTotalUsers').textContent = total;
    if ($('#metricPendingUsers')) $('#metricPendingUsers').textContent = pending;
    if ($('#metricAdminUsers')) $('#metricAdminUsers').textContent = admins;

    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center muted">${isEn ? 'No user records found' : '系統尚無用戶紀錄'}</td></tr>`;
      if (cardsWrapper) cardsWrapper.innerHTML = `<div class="text-center muted">${isEn ? 'No user records found' : '系統尚無用戶紀錄'}</div>`;
      return;
    }

    const tableRows = [];
    const mobileCards = [];

    users.forEach(u => {
      let actionButtons = '';
      if (u.status === 'pending') {
        actionButtons = `
          <button class="btn-sm btn-approve" data-review="approve" data-user="${escapeHtml(u.username)}">${isEn ? '✓ Approve' : '✓ 核准'}</button>
          <button class="btn-sm btn-reject" data-review="reject" data-user="${escapeHtml(u.username)}">${isEn ? '✗ Reject' : '✗ 拒絕'}</button>
          <button class="btn-sm btn-reject" data-deleteuser="${escapeHtml(u.username)}">${isEn ? 'Delete' : '刪除'}</button>
        `;
      } else {
        actionButtons = `
          ${u.role === 'user' ? `<button class="btn-sm btn-action" data-role="admin" data-user="${escapeHtml(u.username)}">${isEn ? 'Promote Admin' : '升為管理員'}</button>` : `<button class="btn-sm btn-warning" data-role="user" data-user="${escapeHtml(u.username)}">${isEn ? 'Demote User' : '降為用戶'}</button>`}
          <button class="btn-sm btn-action" data-resetpass="${escapeHtml(u.username)}">${isEn ? 'Reset Pass' : '重置密碼'}</button>
          <button class="btn-sm btn-reject" data-deleteuser="${escapeHtml(u.username)}">${isEn ? 'Delete' : '刪除'}</button>
        `;
      }

      const tierKey = u.tier || (u.role === 'admin' ? 'admin' : 'teacher_pro');
      const tierSelect = u.role === 'admin'
        ? `<span style="font-size:11px; font-weight:600; color:#d97706;">${isEn ? '👑 Unlimited' : '👑 無限版'}</span>`
        : `
        <select class="admin-tier-select" data-user="${escapeHtml(u.username)}" style="font-size:11px; padding:2px 6px; border-radius:6px; border:1px solid var(--line); background:var(--paper);">
          <option value="teacher_trial" ${tierKey === 'teacher_trial' ? 'selected' : ''}>${isEn ? '🎓 Trial' : '🎓 試用版'}</option>
          <option value="teacher_pro" ${tierKey === 'teacher_pro' ? 'selected' : ''}>${isEn ? '⭐ Pro' : '⭐ 專業版'}</option>
          <option value="institution" ${tierKey === 'institution' ? 'selected' : ''}>${isEn ? '🏫 Institution' : '🏫 機構版'}</option>
        </select>
      `;

      const roleBadge = u.role === 'admin' ? (isEn ? '👑 Admin' : '👑 管理員') : (isEn ? 'User' : '用戶');
      const statusBadge = u.status === 'approved'
        ? (isEn ? 'Approved' : '已開通')
        : (u.status === 'pending' ? (isEn ? '⏳ Pending' : '⏳ 待審核') : (isEn ? 'Rejected' : '已拒絕'));

      const qs = u.quota_summary || { deck_today: 0, deck_limit: 3, ask_today: 0, ask_limit: 10, deck_total: 0, ask_total: 0, is_unlimited: false };

      const dailyUsageHtml = `
        <div style="font-size:11px; line-height:1.4;">
          <div>📊 ${isEn ? 'Decks' : '簡報'}: <b>${qs.deck_today}</b> / ${qs.is_unlimited ? '∞' : qs.deck_limit} ${isEn ? 'items' : '份'}</div>
          <div>💬 ${isEn ? 'Q&A' : '提問'}: <b>${qs.ask_today}</b> / ${qs.is_unlimited ? '∞' : qs.ask_limit} ${isEn ? 'times' : '次'}</div>
        </div>
      `;

      const totalUsageHtml = `
        <div style="font-size:11px; line-height:1.4; color: var(--muted);">
          <div>📊 ${isEn ? 'Decks' : '簡報'}: <b>${qs.deck_total}</b> ${isEn ? 'total' : '份'}</div>
          <div>💬 ${isEn ? 'Q&A' : '提問'}: <b>${qs.ask_total}</b> ${isEn ? 'total' : '次'}</div>
        </div>
      `;

      const lastLoginHtml = `<span style="font-size:11px; color: var(--muted);">${formatLastLoginTime(u.last_login_at)}</span>`;

      tableRows.push(`
        <tr>
          <td>${u.id}</td>
          <td>
            <b>${escapeHtml(u.username)}</b>
            <div style="margin-top: 4px; display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
              <span class="status-chip ${u.status}">${statusBadge}</span>
              <span class="role-chip ${u.role}">${roleBadge}</span>
            </div>
          </td>
          <td>${tierSelect}</td>
          <td>${dailyUsageHtml}</td>
          <td>${totalUsageHtml}</td>
          <td>${lastLoginHtml}</td>
          <td><span style="font-size:11px; color:var(--muted);">${escapeHtml(u.created_at || '-')}</span></td>
          <td>${actionButtons}</td>
        </tr>
      `);

      mobileCards.push(`
        <div class="admin-user-card">
          <div class="user-card-header">
            <div>
              <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                <b class="username">${escapeHtml(u.username)}</b>
                <small class="user-id">#${u.id}</small>
                <div style="margin-left: 2px;">${tierSelect}</div>
              </div>
            </div>
            <div class="badges">
              <span class="status-chip ${u.status}">${statusBadge}</span>
              <span class="role-chip ${u.role}">${roleBadge}</span>
            </div>
          </div>
          <div class="user-card-body">
            <div class="info-item">
              <span class="lbl">${isEn ? 'Daily Usage' : '今日使用 / 限額'}</span>
              <div>${dailyUsageHtml}</div>
            </div>
            <div class="info-item">
              <span class="lbl">${isEn ? 'Cumulative' : '累計總使用量'}</span>
              <div>${totalUsageHtml}</div>
            </div>
            <div class="info-item">
              <span class="lbl">${isEn ? 'Last Active' : '上次上線時間'}</span>
              <div>${lastLoginHtml}</div>
            </div>
            <div class="info-item">
              <span class="lbl">${isEn ? 'Created At' : '帳號建立時間'}</span>
              <div style="font-size:11px; color:var(--muted);">${escapeHtml(u.created_at || '-')}</div>
            </div>
          </div>
          <div class="user-card-actions">
            ${actionButtons}
          </div>
        </div>
      `);
    });

    tbody.innerHTML = tableRows.join('');
    if (cardsWrapper) cardsWrapper.innerHTML = mobileCards.join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">${isEn ? 'Load failed' : '載入失敗'}: ${escapeHtml(err.message)}</td></tr>`;
    if (cardsWrapper) cardsWrapper.innerHTML = `<div class="text-center text-danger">${isEn ? 'Load failed' : '載入失敗'}: ${escapeHtml(err.message)}</div>`;
  }
}

// 代理管理員對話框內的變更層級 (Tier) 動作
$('#adminView')?.addEventListener('change', async (e) => {
  const select = e.target.closest('.admin-tier-select');
  if (select) {
    const username = select.dataset.user;
    const tier = select.value;
    try {
      const res = await api('/api/admin/users/tier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, tier })
      });
      toast(res.message || '用戶層級更新成功');
      fetchAllUsers();
    } catch (err) {
      toast(err.message, true);
    }
  }
});

// 代理管理員對話框內的按鈕動作
$('#adminView')?.addEventListener('click', async (e) => {


  const reviewBtn = e.target.closest('[data-review]');
  if (reviewBtn) {
    const action = reviewBtn.dataset.review;
    const username = reviewBtn.dataset.user;
    try {
      const res = await api('/api/admin/users/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, action })
      });
      toast(res.message);
      fetchAllUsers();
    } catch (err) {
      toast(err.message, true);
    }
    return;
  }

  const roleBtn = e.target.closest('[data-role]');
  if (roleBtn) {
    const role = roleBtn.dataset.role;
    const username = roleBtn.dataset.user;
    try {
      const res = await api('/api/admin/users/role', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, role })
      });
      toast(res.message);
      fetchAllUsers();
    } catch (err) {
      toast(err.message, true);
    }
    return;
  }

  const resetBtn = e.target.closest('[data-resetpass]');
  if (resetBtn) {
    const username = resetBtn.dataset.resetpass;
    const promptMsg = state.lang === 'en' ? `Enter new password for user [${username}]:` : `請輸入為使用者 [${username}] 設定的新密碼：`;
    const newPassword = prompt(promptMsg);
    if (!newPassword) return;
    if (newPassword.length < 4) {
      toast(state.lang === 'en' ? 'New password must be at least 4 characters' : '新密碼長度至少需 4 個字元', true);
      return;
    }
    try {
      const res = await api('/api/admin/users/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, new_password: newPassword })
      });
      toast(res.message);
    } catch (err) {
      toast(err.message, true);
    }
    return;
  }

  const deleteBtn = e.target.closest('[data-deleteuser]');
  if (deleteBtn) {
    const username = deleteBtn.dataset.deleteuser;
    const confirmMsg = state.lang === 'en' ? `Are you sure you want to delete user [${username}]? This action cannot be undone.` : `確定要刪除使用者 [${username}] 嗎？此操作無法復原。`;
    if (!confirm(confirmMsg)) return;
    try {
      const res = await api(`/api/admin/users/${username}`, { method: 'DELETE' });
      toast(res.message);
      fetchAllUsers();
    } catch (err) {
      toast(err.message, true);
    }
    return;
  }
});

// Admin nav button now uses data-view='admin' with switchView
$('#closeAdminModalBtn')?.addEventListener('click', closeAdminModal);
$('#tabPendingUsersBtn')?.addEventListener('click', () => switchAdminTab('pending'));
$('#tabAllUsersBtn')?.addEventListener('click', () => switchAdminTab('all'));

// --- 新增帳號 (管理員開通) Modal 邏輯 ---
function openCreateUserModal() {
  const modal = $('#createUserModal');
  if (modal) {
    modal.classList.remove('hidden');
    $('#createUsernameInput').value = '';
    $('#createPasswordInput').value = '';
    if ($('#createUserError')) $('#createUserError').classList.add('hidden');
  }
}

function closeCreateUserModal() {
  const modal = $('#createUserModal');
  if (modal) modal.classList.add('hidden');
}

$('#openCreateUserModalBtn')?.addEventListener('click', openCreateUserModal);
$('#closeCreateUserModalBtn')?.addEventListener('click', closeCreateUserModal);
$('#createUserModal')?.addEventListener('click', (e) => {
  if (e.target === $('#createUserModal')) closeCreateUserModal();
});

$('#createRoleSelect')?.addEventListener('change', (e) => {
  const isAdmin = e.target.value === 'admin';
  const tierWrapper = $('#createTierWrapper');
  if (tierWrapper) {
    tierWrapper.style.display = isAdmin ? 'none' : 'block';
  }
});

$('#createUserAdminForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = $('#createUsernameInput').value.trim();
  const password = $('#createPasswordInput').value.trim();
  const role = $('#createRoleSelect').value;
  const tier = $('#createTierSelect').value;
  const errEl = $('#createUserError');

  if (errEl) errEl.classList.add('hidden');

  try {
    const res = await api('/api/admin/users/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role, tier })
    });
    toast(res.message || '帳號建立成功');
    closeCreateUserModal();
    fetchAllUsers();
  } catch (err) {
    if (errEl) {
      errEl.textContent = err.message;
      errEl.classList.remove('hidden');
    } else {
      toast(err.message, true);
    }
  }
});

// --- 個人設定 Modal 與修改密碼邏輯 ---

function openProfileModal() {
  if (!state.user) {
    openAuthModal('login');
    return;
  }
  const textEl = $('#profileModalUserText');
  if (textEl) textEl.innerHTML = `目前的登入帳號：<b>${escapeHtml(state.user.username)}</b> (${state.user.role === 'admin' ? '👑 管理員' : '一般用戶'})`;
  if ($('#changePassError')) $('#changePassError').classList.add('hidden');
  if ($('#changePassSuccess')) $('#changePassSuccess').classList.add('hidden');
  const modal = $('#profileModal');
  if (modal) modal.classList.remove('hidden');
}

function closeProfileModal() {
  const modal = $('#profileModal');
  if (modal) modal.classList.add('hidden');
}

$('#closeProfileModalBtn')?.addEventListener('click', closeProfileModal);
$('#profileModal')?.addEventListener('click', (e) => {
  if (e.target === $('#profileModal')) closeProfileModal();
});

$('#profileLogoutBtn')?.addEventListener('click', () => {
  closeProfileModal();
  logoutUser(true);
});

$('#changePasswordForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const oldPassword = $('#oldPasswordInput').value;
  const newPassword = $('#newPasswordInput').value;
  const errorEl = $('#changePassError');
  const successEl = $('#changePassSuccess');

  errorEl.classList.add('hidden');
  successEl.classList.add('hidden');

  try {
    const res = await api('/api/user/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    });
    successEl.textContent = res.message;
    successEl.classList.remove('hidden');
    $('#oldPasswordInput').value = '';
    $('#newPasswordInput').value = '';
    toast(state.lang === 'en' ? 'Password changed successfully' : '密碼已成功修改');
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
});

// 頁面初始化語系
setLanguage(state.lang);

// === Agent Ops Command Center Logic (Chat Stream UX) ===
const DEPT_WELCOME_CONFIGS = {
  academic: {
    avatar: '🎓',
    title: { 'zh-TW': '💡 歡迎與教務小老師對話', 'en': '💡 Welcome to LessonFlow Tutor' },
    desc: { 'zh-TW': '請下達備課或教學任務（例如：「設計牛頓運動定律 45 分鐘教案」、「出 5 題高中生物題」或「生成逐頁演講稿」）。', 'en': 'Enter lesson plan or teaching tasks (e.g. "Design a 45-min Physics plan", "Generate 5 Biology quiz questions").' },
    suggestions: [
      { text: '🎓 45 分鐘教案設計', query: '請幫我設計一份 45 分鐘國中物理「牛頓第二運動定律」的備課教案與觀念大綱' },
      { text: '📝 5 題生物選擇題與解析', query: '請幫我出 5 題關於「光合作用與呼吸作用」的高中生物選擇題，包含解答與觀念解析' },
      { text: '🎤 簡報逐頁演講稿', query: '請幫我生成這份簡報的逐頁演講稿與備課講義' }
    ]
  },
  marketing: {
    avatar: '🚀',
    title: { 'zh-TW': '🚀 歡迎與營銷推廣專員對話', 'en': '🚀 Welcome to Marketing Specialist' },
    desc: { 'zh-TW': '請下達推廣或文案任務（例如：「撰寫微課教學 FB 貼文」、「梳理課程核心賣點」或「撰寫教學心得文章」）。', 'en': 'Enter marketing tasks (e.g. "Write an FB promo post", "Summarize course pitch features").' },
    suggestions: [
      { text: '📱 FB / Threads 社群推廣貼文', query: '請幫我產出一篇介紹微課教學與防幻覺 AI 助手的 FB 社群推廣文案' },
      { text: '🎯 梳理課程亮點與賣點', query: '請幫我梳理這份數位課程的核心賣點與亮點介紹' },
      { text: '✍️ 撰寫教學心得體驗文章', query: '請幫我撰寫一篇分享翻轉課堂實務心得的教學經驗文章' }
    ]
  },
  operations: {
    avatar: '🏫',
    title: { 'zh-TW': '🏫 歡迎與教務行政特助對話', 'en': '🏫 Welcome to Operations Assistant' },
    desc: { 'zh-TW': '請下達行政或權限查詢任務（例如：「查詢學校團體合約」、「檢視團隊席位配額」或「查詢個人每日限額」）。', 'en': 'Enter admin tasks (e.g. "Check school contract terms", "View team seat allocation").' },
    suggestions: [
      { text: '🏫 查詢機構與學校團體合約', query: '查詢學校與機構團體授權合約與成員開通方式' },
      { text: '📊 檢視團隊席位分配與權限', query: '檢視團隊成員席位分配與權限開通規則' },
      { text: '📋 查詢個人每日配額與等級', query: '查詢我目前的會員等級與每日使用配額' }
    ]
  },
  devops: {
    avatar: '🛠️',
    title: { 'zh-TW': '🛠️ 歡迎與技術維護工程師對話', 'en': '🛠️ Welcome to DevOps Engineer' },
    desc: { 'zh-TW': '請下達維護或診斷任務（例如：「排查 Railway 部署狀態」、「診斷 Linux OOM 記憶體效能」或「檢視 JWT 驗證」）。', 'en': 'Enter devops tasks (e.g. "Check Railway deploy health", "Diagnose Linux Kernel OOM memory").' },
    suggestions: [
      { text: '🛠️ 排查 Railway 雲端部署狀態', query: '排查本機與 Railway 雲端部署運行狀態與環境設定' },
      { text: '⚡ 診斷 Linux Kernel OOM 效能', query: '診斷 Linux Kernel OOM 記憶體排查與系統效能最佳化' },
      { text: '🔑 檢視 JWT 驗證與過期機制', query: '檢視系統 JWT 身份驗證機制與 Token 過期設定' }
    ]
  }
};

function updateAgentDeptBar(deptKey) {
  const isEn = state.lang === 'en';
  const deptLabels = {
    academic: isEn ? '🎓 Academic & Teaching (LessonFlow Tutor)' : '🎓 教務教學部（教務小老師）',
    marketing: isEn ? '🚀 Marketing & Sales (Marketing Specialist)' : '🚀 市場與營銷部（營銷推廣專員）',
    operations: isEn ? '🏫 Operations & Admin (Operations Assistant)' : '🏫 營運與行政部（教務行政特助）',
    devops: isEn ? '🛠️ DevOps & Infra (DevOps Engineer)' : '🛠️ 技術維護部（技術維護工程師）'
  };
  const titleEl = $('#agentDeptBarTitle');
  if (titleEl) {
    titleEl.textContent = deptLabels[deptKey] || (isEn ? '🌐 Omni-Routing Mode' : '🌐 全域智慧導航模式');
  }
  $$('.dept-switch-chip').forEach(chip => {
    chip.classList.toggle('active', chip.dataset.dept === deptKey);
  });
}

function toggleAgentDeptDrawer(collapse) {
  const drawer = $('#agentDeptDrawer');
  const agentView = $('#agentView');
  const toggleBtn = $('#agentDeptToggleBtn');
  const toggleText = $('#agentDeptToggleText');
  const toggleIcon = toggleBtn?.querySelector('.toggle-icon');
  if (!drawer) return;

  const willCollapse = collapse !== undefined ? collapse : !drawer.classList.contains('collapsed');
  if (willCollapse) {
    drawer.classList.add('collapsed');
    agentView?.classList.add('drawer-collapsed');
    if (toggleText) toggleText.textContent = t('agent.toggle_expand');
    if (toggleIcon) toggleIcon.textContent = '▼';
  } else {
    drawer.classList.remove('collapsed');
    agentView?.classList.remove('drawer-collapsed');
    if (toggleText) toggleText.textContent = t('agent.toggle_collapse');
    if (toggleIcon) toggleIcon.textContent = '▲';
  }
}

function switchAgentDeptWelcome(deptKey) {
  const lang = state.lang || 'zh-TW';
  const container = $('#agentMessages');

  // 若重複點擊當前已鎖定的部門，則切換取消指定分流，回到全域智慧導航模式
  if (state.activeDept === deptKey) {
    state.activeDept = null;
    renderDeptActiveIndicators();
    updateAgentDeptBar(null);

    if (container) {
      const sysMsgEl = document.createElement('div');
      sysMsgEl.className = 'message assistant system-dept-switch';
      sysMsgEl.style.borderLeft = '4px solid #10b981';
      sysMsgEl.style.background = 'rgba(16, 185, 129, 0.05)';
      sysMsgEl.innerHTML = `
        <span class="bot-avatar" style="background: #10b981;">🌐</span>
        <div>
          <div class="agent-msg-meta">
            <span class="agent-dept-chip" style="background: rgba(16, 185, 129, 0.2); color: #059669;">🌐 ${lang === 'en' ? 'Omni-Routing Mode' : '全域智慧導航模式'}</span>
          </div>
          <p style="margin: 4px 0 0 0; color: var(--fg); font-weight: 500;">
            ${lang === 'en' ? 'Department restriction cleared. Orchestrator will now auto-route all queries dynamically.' : '已取消指定部門分流！系統現已切換回【全域智慧導航模式】，將自動辨識問題意圖並分發給最適切的部門。'}
          </p>
        </div>
      `;
      container.appendChild(sysMsgEl);
      container.scrollTop = container.scrollHeight;
    }
    toast(lang === 'en' ? 'Switched to Omni-Routing Mode' : '已取消指定分流，回到全域智慧導航模式！');
    return;
  }

  // 否則，鎖定指定部門
  state.activeDept = deptKey;
  renderDeptActiveIndicators();
  updateAgentDeptBar(deptKey);
  const cfg = DEPT_WELCOME_CONFIGS[deptKey] || DEPT_WELCOME_CONFIGS.academic;
  if (!container) return;

  const titleText = cfg.title[lang] || cfg.title['zh-TW'];
  const descText = cfg.desc[lang] || cfg.desc['zh-TW'];
  const sugHtml = cfg.suggestions.map(s => `<button type="button" class="agent-sug-btn" data-query="${escapeHtml(s.query)}">${escapeHtml(s.text)}</button>`).join('');

  // 建立接續對話的部門切換指示卡片 (不覆蓋歷史訊息，直接接續對話流)
  const sysMsgEl = document.createElement('div');
  sysMsgEl.className = 'message assistant system-dept-switch';
  sysMsgEl.style.borderLeft = '4px solid #6366f1';
  sysMsgEl.style.background = 'rgba(99, 102, 241, 0.05)';
  sysMsgEl.innerHTML = `
    <span class="bot-avatar" style="background: #6366f1;">${cfg.avatar}</span>
    <div>
      <div class="agent-msg-meta">
        <span class="agent-dept-chip" style="background: rgba(99, 102, 241, 0.2); color: #4f46e5;">🎯 ${escapeHtml(titleText)}</span>
      </div>
      <p style="margin: 4px 0 8px 0; color: var(--fg); font-weight: 500;">${escapeHtml(descText)}</p>
      <div class="suggestions" style="margin-top: 8px;">${sugHtml}</div>
    </div>
  `;

  container.appendChild(sysMsgEl);
  container.scrollTop = container.scrollHeight;

  const deptNames = {
    academic: lang === 'en' ? '🎓 LessonFlow Tutor' : '🎓 教務小老師',
    marketing: lang === 'en' ? '🚀 Marketing Specialist' : '🚀 營銷推廣專員',
    operations: lang === 'en' ? '🏫 Operations Assistant' : '🏫 教務行政特助',
    devops: lang === 'en' ? '🛠️ DevOps Engineer' : '🛠️ 技術維護工程師'
  };
  const label = deptNames[deptKey] || deptNames.academic;
  toast(lang === 'en' ? `Connected to ${label}` : `已切換至【${label}】專屬對話視窗！`);
}

document.addEventListener('click', (e) => {
  const deptCard = e.target.closest('.agent-dept-card');
  if (deptCard && deptCard.dataset.dept) {
    if (deptCard.getAttribute('data-disabled') === 'true') {
      const isEn = state.lang === 'en';
      toast(isEn ? 'This department requires admin permissions.' : '此部門為管理員專用，請先取得授權');
      return;
    }
    switchAgentDeptWelcome(deptCard.dataset.dept);
    toggleAgentDeptDrawer(true);
  }

  const switchChip = e.target.closest('.dept-switch-chip');
  if (switchChip && switchChip.dataset.dept) {
    switchAgentDeptWelcome(switchChip.dataset.dept);
  }

  const deptToggleBtn = e.target.closest('#agentDeptToggleBtn');
  if (deptToggleBtn) {
    toggleAgentDeptDrawer();
  }

  const deptExpandBtn = e.target.closest('#agentDeptExpandBtn');
  if (deptExpandBtn) {
    toggleAgentDeptDrawer(false);
  }

  const topbarCollapse = e.target.closest('#topbarCollapseBtn');
  if (topbarCollapse) {
    toggleTopbar(true);
  }

  const topbarRestore = e.target.closest('#topbarRestoreBtn');
  if (topbarRestore) {
    toggleTopbar(false);
  }

  const btn = e.target.closest('.agent-sug-btn, .skill-chip-btn');
  if (btn && btn.dataset.query) {
    const input = $('#agentQueryInput');
    if (input) input.value = btn.dataset.query;
    dispatchAgentTask(btn.dataset.query);
  }

  const copyBtn = e.target.closest('.agent-copy-btn');
  if (copyBtn && copyBtn.dataset.copy) {
    navigator.clipboard.writeText(copyBtn.dataset.copy).then(() => {
      toast(state.lang === 'en' ? 'Copied to clipboard!' : '已複製內容至剪貼簿！');
    });
  }

  const profileRefresh = e.target.closest('#profileRefreshBtn');
  if (profileRefresh) {
    if (typeof fetchUserProfile === 'function') {
      fetchUserProfile().then(() => {
        renderProfileView();
        toast(t('toast.profile_refreshed') || (state.lang === 'en' ? 'Account info updated' : '帳號資訊已更新'));
      });
    }
  }

  const previewTabBtn = e.target.closest('.preview-tab-btn');
  if (previewTabBtn && previewTabBtn.dataset.previewTab) {
    if (typeof switchPreviewTab === 'function') {
      switchPreviewTab(previewTabBtn.dataset.previewTab);
    }
  }

  const disabledDownloadBtn = e.target.closest('#deckView .download-actions a.disabled, #deckView .download-actions button.disabled');
  if (disabledDownloadBtn) {
    e.preventDefault();
    const isEn = state.lang === 'en';
    toast(isEn ? 'Please generate materials in Workspace first!' : '尚未生成相關內容，請先在工作台生成！', true);
  }
});

$('#agentForm')?.addEventListener('submit', (e) => {
  e.preventDefault();
  const input = $('#agentQueryInput');
  const query = input?.value?.trim();
  if (query) {
    dispatchAgentTask(query);
    if (input) {
      input.value = '';
      input.style.height = 'auto';
    }
  }
});

$('#agentQueryInput')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    $('#agentForm')?.requestSubmit();
  }
});

function autoResizeTextarea(el) {
  if (!el) return;
  el.style.height = 'auto';
  const maxHeight = Math.floor(window.innerHeight * 0.48);
  const newHeight = Math.min(Math.max(el.scrollHeight, 44), maxHeight);
  el.style.height = newHeight + 'px';
}

['agentQueryInput', 'questionInput'].forEach(id => {
  const el = $(`#${id}`);
  if (el) {
    el.addEventListener('input', () => autoResizeTextarea(el));
    el.addEventListener('focus', () => autoResizeTextarea(el));
    el.addEventListener('change', () => autoResizeTextarea(el));
  }
});

// 清空 AI 備課助手對話紀錄按鈕
$('#clearAgentChatBtn')?.addEventListener('click', () => {
  const dept = state.activeDept || 'academic';
  if (!state.agentHistoryByDept) state.agentHistoryByDept = {};
  state.agentHistoryByDept[dept] = [];
  state.agentHistory = [];
  const container = $('#agentMessages');
  if (container) {
    const isEn = state.lang === 'en';
    container.innerHTML = `
      <div class="message assistant welcome">
        <span class="bot-avatar">✦</span>
        <div>
          <b data-i18n="agent.welcome_title">${isEn ? '💡 Welcome to AI Lesson Assistant' : '💡 歡迎使用 AI 備課助手'}</b>
          <p data-i18n="agent.welcome_desc">${isEn ? 'Enter any lesson plan or teaching task (e.g. "Design a 45-min Physics lesson plan", "Generate 5 Biology quiz questions", or "Write a teaching post").' : '請下達備課或教學任務（例如：「設計牛頓運動定律 45 分鐘教案」、「出 5 題高中生物題」或「寫一篇教學心得」）。'}</p>
          <div class="suggestions">
            <button type="button" class="agent-sug-btn" data-query="請幫我設計一份 45 分鐘國中物理「牛頓第二運動定律」的備課教案與觀念大綱">🎓 45 分鐘教案設計</button>
            <button type="button" class="agent-sug-btn" data-query="請幫我出 5 題關於「光合作用與呼吸作用」的高中生物選擇題，包含解答與觀念解析">📝 5 題生物選擇題與解析</button>
            <button type="button" class="agent-sug-btn" data-query="請幫我產出一篇介紹 Self-RAG 防幻覺功能的 FB 社群推廣文案">🚀 FB/Threads 社群推廣文案</button>
            <button type="button" class="agent-sug-btn" data-query="查詢我目前的會員等級與每日使用配額">📋 查詢會員等級與每日配額</button>
          </div>
        </div>
      </div>
    `;
  }
  toast(state.lang === 'en' ? 'Department conversation reset.' : '已重置當前助手對話紀錄！');
});

async function dispatchAgentTask(query) {
  const isEn = state.lang === 'en';
  if (!state.user) {
    toast(isEn ? 'Please log in to use the AI Agent Assistant' : '請先登入帳號以開始問答與使用備課助手', true);
    openAuthModal('login');
    return;
  }

  if (!state.agentHistoryByDept) state.agentHistoryByDept = { academic: [], marketing: [], operations: [], devops: [] };
  const activeDept = state.activeDept || 'academic';
  if (!state.agentHistoryByDept[activeDept]) state.agentHistoryByDept[activeDept] = [];

  const container = $('#agentMessages');
  const sendBtn = $('#agentSendBtn');
  const queryInput = $('#agentQueryInput');
  const platform = 'FB / 社群媒體';

  if (queryInput) queryInput.value = '';
  if (!container) return;

  // 紀錄對話歷程 (User Turn)
  state.agentHistoryByDept[activeDept].push({ role: 'user', content: query });
  state.agentHistory = state.agentHistoryByDept[activeDept];

  // 1. Append User Message Bubble
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'message user';
  userMsgEl.innerHTML = `<div><b>${escapeHtml(query)}</b></div>`;
  container.appendChild(userMsgEl);

  // 2. Append Assistant Loading Bubble with Multi-stage Pipeline
  const agentStages = isEn ? [
    { text: 'Analyzing task intent & routing to specialized department...' },
    { text: 'AI Specialist generating lesson design & pedagogical structure...' },
    { text: 'Reviewing educational quality & logical consistency...' }
  ] : [
    { text: '分析任務意圖與調度專屬部門...' },
    { text: 'AI 專家正在構思教學設計與方案內容...' },
    { text: '執行教學品質與邏輯一致性審查...' }
  ];

  const assistantMsgEl = document.createElement('div');
  assistantMsgEl.className = 'message assistant loading-turn';
  assistantMsgEl.innerHTML = `
    <span class="bot-avatar">✦</span>
    <div>
      <div class="agent-msg-meta">
        <span class="agent-dept-chip">${isEn ? '⏳ Dispatching...' : '⏳ 正在分發...'}</span>
      </div>
      <div class="stage-pipeline" id="agentStagePipeline"></div>
    </div>
  `;
  container.appendChild(assistantMsgEl);
  container.scrollTop = container.scrollHeight;
  if (sendBtn) sendBtn.disabled = true;

  const agentPipelineContainer = assistantMsgEl.querySelector('#agentStagePipeline');
  const agentPipeline = createStagePipeline(agentPipelineContainer, agentStages);

  try {
    const res = await api('/api/agent/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        platform,
        target_department: state.activeDept || null,
        history: state.agentHistoryByDept[activeDept].slice(-10)
      })
    });
    agentPipeline.finish();
    await new Promise(r => setTimeout(r, 200));
    assistantMsgEl.classList.remove('loading-turn');

    const dept = res.department ? res.department.toUpperCase() : 'GENERAL';
    const skill = res.matched_skill || 'general';
    const data = res.data || {};
    const text = (typeof data === 'object' ? (data.output_text || data.copywriting || JSON.stringify(data, null, 2)) : String(data)) || res.message || (isEn ? 'Task completed.' : '任務完成。');

    // 紀錄對話歷程 (Assistant Turn)
    state.agentHistoryByDept[activeDept].push({ role: 'assistant', content: text });

    const deptLabels = {
      'ACADEMIC': isEn ? '🎓 Academic & Teaching' : '🎓 教務教學部',
      'OPERATIONS': isEn ? '📋 Operations & Admin' : '📋 營運與行政部',
      'DEVOPS': isEn ? '🛠️ DevOps & Infra' : '🛠️ 技術維護部',
      'MARKETING': isEn ? '🚀 Marketing & Sales' : '🚀 市場與營銷部'
    };
    const deptLabel = deptLabels[dept] || (isEn ? `🎯 Dept: ${dept}` : `🎯 部門: ${dept}`);

    // 動態生成備課助手的後續延伸建議膠囊
    let agentFollowUps = [];
    if (dept === 'ACADEMIC' || dept === 'GENERAL') {
      agentFollowUps = isEn ? [
        { label: '📑 Add 5 Quiz Questions', query: 'Based on this lesson outline, generate 5 multiple-choice quiz questions with detailed explanations.' },
        { label: '🎯 Add Classroom Activities', query: 'Suggest 2 engaging interactive classroom activities and discussion questions for students.' },
        { label: '🗣️ Oral Lecture Script', query: 'Please rewrite this into a step-by-step oral lecture teaching script with smooth transitions.' }
      ] : [
        { label: '📑 延伸設計 5 題評量測驗', query: '請依據剛才設計的教案大綱，進一步出 5 題單選測驗題並附上詳細解析。' },
        { label: '🎯 補充課堂互動與提問', query: '請為這個單元設計 2 個引導學生思考的課堂提問與分組互動環節。' },
        { label: '🗣️ 轉換為逐頁口語講稿', query: '請將這份教案大綱轉換為教師授課時可直接口述的口語化教學講稿。' }
      ];
    } else if (dept === 'MARKETING') {
      agentFollowUps = isEn ? [
        { label: '🚀 Short Video Script', query: 'Convert this marketing copy into a 60-second engaging short video script (Reels/TikTok).' },
        { label: '📢 High-converting Headlines', query: 'Generate 5 alternative high-converting click-worthy post titles.' }
      ] : [
        { label: '🚀 產出 60 秒短影音腳本', query: '請將這篇招生文案轉化為 60 秒吸引人的 Reels/Shorts 短影音分鏡腳本。' },
        { label: '📢 提供 5 組吸睛吸粉標題', query: '請提供 5 組不同風格、高點閱率的社群貼文吸睛主標題。' }
      ];
    }

    const followUpHtml = agentFollowUps.length ? `
      <div class="follow-up-suggestions">
        <div class="follow-up-label">
          <span>⚡</span> <span>${isEn ? 'Suggested Next Steps (Context-Aware):' : '推薦接續任務（延續備課脈絡）：'}</span>
        </div>
        ${agentFollowUps.map(c => `<button type="button" class="follow-up-chip agent-sug-btn" data-query="${escapeHtml(c.query)}">${escapeHtml(c.label)}</button>`).join('')}
      </div>
    ` : '';

    // 3. Replace Loading with Final Assistant Response Bubble (Rendered with Markdown & Math)
    const showPptxBtn = (dept === 'ACADEMIC' || dept === 'GENERAL');
    assistantMsgEl.innerHTML = `
      <span class="bot-avatar">✦</span>
      <div>
        <div class="agent-msg-meta">
          <span class="agent-dept-chip">${deptLabel}</span>
          <span class="agent-skill-chip">⚡ Skill: ${skill}</span>
        </div>
        <div class="agent-output-content">${renderMarkdownToHtml(text)}</div>
        ${followUpHtml}
        <div class="agent-action-bar" style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
          <button type="button" class="agent-action-btn agent-copy-btn" data-copy="${escapeHtml(text)}">${isEn ? '📋 Copy Content' : '📋 複製內容'}</button>
          ${showPptxBtn ? `<button type="button" class="agent-action-btn agent-pptx-btn" data-query="${escapeHtml(query)}" data-copy="${escapeHtml(text)}">${isEn ? '📄 Import to Workspace' : '📄 導入教案工作台'}</button>` : ''}
        </div>
      </div>
    `;

    renderMath(assistantMsgEl);

    toast(isEn ? `Task completed by ${deptLabel}` : `Agent 任務已由 ${deptLabel} 順利完成`);
    await fetchCurrentUser();
  } catch (err) {
    agentPipeline.destroy();
    assistantMsgEl.classList.remove('loading-turn');
    assistantMsgEl.innerHTML = `
      <span class="bot-avatar" style="background: #f87171; color: #fff;">!</span>
      <div>
        <div class="agent-msg-meta">
          <span class="agent-dept-chip" style="background: rgba(239, 68, 68, 0.1); color: #dc2626;">${isEn ? '🔴 Dispatch Failed' : '🔴 處理失敗'}</span>
        </div>
        <p style="color: #dc2626; margin: 0;">❌ ${isEn ? 'Error:' : '錯誤：'}${escapeHtml(err.message)}</p>
      </div>
    `;
    toast(err.message, true);
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    container.scrollTop = container.scrollHeight;
  }
}

function extractCleanDocTitle(query, content) {
  // 1. 優先匹配專有名詞引號內的主題（如：「牛頓第二運動定律」、「光合作用與呼吸作用」）
  const quoteMatch = (query || '').match(/[「『"']([^「」『』"']{2,25})[」』"']/);
  if (quoteMatch && quoteMatch[1].trim()) {
    return quoteMatch[1].trim();
  }

  // 2. 掃描 AI 產出內容的前 8 列，萃取 Markdown 大綱標題 (# 主題 或 **主題**)
  if (content) {
    const lines = content.split('\n').slice(0, 8);
    for (let line of lines) {
      line = line.trim();
      const headerMatch = line.match(/^(?:#+\s*|\*\*)([^\n\*#]{2,30})(?:\*\*|\n)?/);
      if (headerMatch && headerMatch[1].trim()) {
        let t = headerMatch[1].trim().replace(/[\\/:*?"<>|]/g, '');
        t = t.replace(/^(備課教案|教案大綱|教案|備課大綱|課程大綱|教學主題)[:：\s]*/g, '');
        if (t.length >= 2 && t.length <= 25 && !t.includes('請幫我')) return t;
      }
    }
  }

  // 3. 提問動詞與贅字剝離演算法
  let clean = (query || 'AI_備課教案').trim();
  clean = clean.replace(/^(請|幫我|請幫我|需要|設計|撰寫|產出|產生|寫一篇|出\s*\d+\s*題|關於|查詢)+/g, '');
  clean = clean.replace(/(的一份|一份|關於)+/g, '');
  clean = clean.replace(/(的備課教案與觀念大綱|的備課教案|的教案大綱|教案大綱|教案|的宣傳文案|推廣文案|的教學心得文章|教學經驗文章|選擇題與解析|選擇題|大綱)$/g, '');
  clean = clean.replace(/[「」『』""'']/g, '');

  clean = clean.trim();
  if (clean.length > 20) {
    clean = clean.split(/(的|與|及|包含|包含解答)/)[0];
  }

  return clean.slice(0, 20).trim() || 'AI_備課教材';
}

// 處理 Agent 產出卡片的操作按鈕 (將生成結果當成教材導入，切換至教材解析頁面並顯示解析等待畫面)
document.addEventListener('click', async (e) => {
  const pptxBtn = e.target.closest('.agent-pptx-btn');
  if (pptxBtn) {
    const isEn = state.lang === 'en';
    const topic = pptxBtn.getAttribute('data-query') || 'AI_備課教案';
    const msgBox = pptxBtn.closest('.message');
    const copyBtn = msgBox ? msgBox.querySelector('.agent-copy-btn') : null;
    const content = pptxBtn.getAttribute('data-copy') || copyBtn?.getAttribute('data-copy') || msgBox?.querySelector('.agent-output-content')?.innerText || '';

    if (!content) {
      switchView('workspace');
      toast(isEn ? 'Switched to Material Parsing' : '已切換至【📄 教材解析】！');
      return;
    }

    // 1. 先切換至【📄 教材解析】頁面
    switchView('workspace');

    // 2. 觸發標準教材解析中的全螢幕/等待動畫畫面
    loading(
      true,
      isEn ? 'Parsing & Indexing Material...' : '正在解析與索引備課教材中...',
      isEn ? 'AI is chunking markdown content, extracting LaTeX formulas, and indexing knowledge vector database...' : '系統正在切割 Markdown 教案段落、建立 LaTeX 數學公式與轉譯知識向量庫，請稍候...'
    );

    try {
      // 3. 提取精簡標題，呼叫後端 API 將生成結果導入為 Document
      const cleanTitle = extractCleanDocTitle(topic, content);
      const doc = await api('/api/documents/import_text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: cleanTitle, content: content })
      });

      // 4. 設定已上傳/解析完成的 Document 狀態
      setDocument(doc);

      const fileCard = $('#fileCard');
      if (fileCard) fileCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

      toast(isEn
        ? '🎉 Material imported successfully! Proceed with standard parsing and lesson design.'
        : '🎉 已將生成結果成功導入為教材！已為您完成解析並進入教材工作區。'
      );
    } catch (err) {
      toast(err.message || (isEn ? 'Import failed' : '導入教材失敗'), true);
    } finally {
      loading(false);
    }
    return;
  }
});

// === 3合1 Workspace 並行生成與模組處理邏輯 ===

function setBtnLoading(btn, isLoading, originalHtml) {
  if (!btn) return;
  btn.disabled = isLoading;
  const spinner = btn.querySelector('.btn-inline-spinner');
  const lbl = btn.querySelector('.btn-lbl') || btn.querySelector('[data-i18n]');

  if (spinner) {
    spinner.classList.toggle('hidden', !isLoading);
  }

  if (lbl) {
    if (isLoading) {
      if (!lbl.dataset.origText) lbl.dataset.origText = lbl.textContent;
      lbl.textContent = state.lang === 'en' ? 'Generating...' : '生成中...';
    } else {
      const i18nKey = lbl.dataset.i18n;
      if (i18nKey && typeof t === 'function' && t(i18nKey)) {
        lbl.textContent = t(i18nKey);
      } else if (lbl.dataset.origText) {
        lbl.textContent = lbl.dataset.origText;
      }
      delete lbl.dataset.origText;
    }
  } else {
    if (isLoading) {
      if (!btn.dataset.origText) btn.dataset.origText = btn.textContent;
      btn.innerHTML = `<span class="btn-inline-spinner"></span> ${state.lang === 'en' ? 'Generating...' : '生成中...'}`;
    } else {
      btn.innerHTML = btn.dataset.origText || originalHtml || (state.lang === 'en' ? 'Generate' : '生成');
      delete btn.dataset.origText;
    }
  }
}

function updateModuleStatusChip(chipId, status, text, onClick) {
  const chip = $(`#${chipId}`);
  if (!chip) return;
  chip.className = `module-status-chip ${status}`;
  chip.textContent = text;
  chip.onclick = onClick || null;
}

function getHandoutTextForContext() {
  if (!state.handout) return null;
  const h = state.handout;
  let text = `# ${h.title || '教學講義'}\n${h.subtitle || ''}\n\n## 課程總覽\n${h.overview || ''}\n\n`;
  if (Array.isArray(h.sections)) {
    h.sections.forEach((s, idx) => {
      text += `### 第 ${idx + 1} 節：${s.title || ''}\n${s.summary || ''}\n`;
      if (Array.isArray(s.key_points)) {
        text += s.key_points.map(kp => `- ${kp}`).join('\n') + '\n';
      }
      text += '\n';
    });
  }
  if (Array.isArray(h.key_takeaways)) {
    text += `## 核心總結\n` + h.key_takeaways.map(t => `- ${t}`).join('\n') + '\n';
  }
  return text.trim();
}

// 1. 教學簡報 (Deck) 生成 Action
async function generateDeckAction(silent = false, showOverlay = true) {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in first' : '請先登入帳號', true);
    openAuthModal('login');
    return false;
  }
  if (!state.document) {
    toast(state.lang === 'en' ? 'Please upload a material first' : '請先上傳教材', true);
    return false;
  }

  const btn = $('#generateBtn');
  setBtnLoading(btn, true);
  updateModuleStatusChip(
    'deckStatusChip',
    'running',
    state.lang === 'en' ? 'Generating deck...' : '簡報生成中...'
  );

  const audience = $('#audience') ? $('#audience').value : '一般大眾/初學者';
  const tone = $('#tone') ? $('#tone').value : '清楚易懂';
  const language = $('#targetLanguage') ? $('#targetLanguage').value : 'auto';
  const duration = +($('#duration')?.value || 30);
  const slide_count = +($('#slideCount')?.value || 8);
  const enable_web_search = $('#deckWebSearch') ? $('#deckWebSearch').checked : false;
  const handoutText = getHandoutTextForContext();

  if (showOverlay) {
    const isEn = state.lang === 'en';
    loading(
      true,
      isEn ? 'Generating Teaching Deck & Script...' : '正在生成教學簡報與逐頁講稿…',
      isEn ? 'Planning slide outline and pedagogical structure…' : `正在以【${tone}】風格規劃簡報大綱與架構…`,
      isEn ? [
        `Tailoring content for ${audience}…`,
        `Writing speaker notes with ${tone} tone…`,
        'Verifying hallucination guardrails & KaTeX math…',
        'Finalizing slides, icons, and visual layout…'
      ] : [
        `針對【${audience}】精準調校教學內容深度…`,
        `以【${tone}】風格撰寫逐頁演講稿與導讀…`,
        '進行數學與理化公式 LaTeX 格式校驗…',
        '即將完成教學簡報，準備呈現…'
      ]
    );
  }

  const payload = {
    document_id: state.document.id,
    audience,
    tone,
    language,
    duration,
    slide_count,
    enable_web_search,
    handout_text: handoutText || undefined,
  };

  try {
    const deck = await api('/api/decks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    state.deck = deck;
    saveWorkspaceStateToStorage();
    renderDeck();
    updatePreviewCountBadge();
    $$('.step')[1]?.classList.add('done');
    $$('.step')[2]?.classList.add('active', 'done');
    await fetchCurrentUser();

    updateModuleStatusChip(
      'deckStatusChip',
      'success',
      state.lang === 'en' ? '✓ Deck Ready (Click to View)' : '✓ 簡報已就緒 (點擊查看)',
      () => { switchView('deck'); switchPreviewTab('deck'); }
    );

    if (!silent) {
      toast(state.lang === 'en' ? 'Deck and speaker notes are ready!' : '簡報與逐頁講稿已經準備好了');
      switchView('deck');
      switchPreviewTab('deck');
    }
    return true;
  } catch (err) {
    updateModuleStatusChip(
      'deckStatusChip',
      'error',
      state.lang === 'en' ? '✗ Deck generation failed' : '✗ 簡報生成失敗'
    );
    await fetchCurrentUser();
    toast(err.message || (state.lang === 'en' ? 'Deck generation failed' : '簡報生成失敗'), true);
    return false;
  } finally {
    setBtnLoading(btn, false);
    if (showOverlay) loading(false);
  }
}

// 2. 隨堂講義 (Handout) 生成 Action
async function generateHandoutAction(silent = false, showOverlay = true) {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in first' : '請先登入帳號', true);
    openAuthModal('login');
    return false;
  }
  if (!state.document) {
    toast(state.lang === 'en' ? 'Please upload a material first' : '請先上傳教材', true);
    return false;
  }

  const btn = $('#generateHandoutBtn');
  setBtnLoading(btn, true);
  updateModuleStatusChip(
    'handoutStatusChip',
    'running',
    state.lang === 'en' ? 'Generating handout...' : '講義生成中...'
  );

  const audience = $('#audience') ? $('#audience').value : '一般大眾/初學者';
  const tone = $('#tone') ? $('#tone').value : '清楚易懂';
  const language = $('#targetLanguage') ? $('#targetLanguage').value : 'auto';
  const detail_level = $('#handoutDetail') ? $('#handoutDetail').value : 'standard';
  const enable_web_search = $('#handoutWebSearch') ? $('#handoutWebSearch').checked : false;

  if (showOverlay) {
    const isEn = state.lang === 'en';
    loading(
      true,
      isEn ? 'Generating A4 Study Handout...' : '正在生成 A4 隨堂講義與導讀…',
      isEn ? 'Analyzing textbook and structuring core concepts…' : `正在以【${tone}】風格分析教材並規劃導讀章節…`,
      isEn ? [
        `Customizing narrative for ${audience}…`,
        `Applying ${tone} storytelling & vivid metaphors…`,
        'Formatting formulas with standard LaTeX…',
        'Designing scenario-based inquiry questions…',
        'Finalizing printable A4 layout…'
      ] : [
        `為【${audience}】量身打造章節導讀與複習重點…`,
        `貫徹【${tone}】風格與生活化比喻…`,
        '精確排版理化與數理 LaTeX 公式…',
        '設計情境探究式思考與討論題…',
        '即將完成 A4 隨堂講義排版…'
      ]
    );
  }

  try {
    const handout = await api('/api/handouts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: state.document.id,
        target_audience: audience,
        audience,
        tone,
        language,
        detail_level,
        enable_web_search,
      })
    });
    state.handout = handout;
    saveWorkspaceStateToStorage();
    updatePreviewCountBadge();
    await fetchCurrentUser();
    renderHandoutPreview();

    updateModuleStatusChip(
      'handoutStatusChip',
      'success',
      state.lang === 'en' ? '✓ Handout Ready (Click to View)' : '✓ 講義已就緒 (點擊查看)',
      () => { switchView('deck'); switchPreviewTab('handout'); }
    );

    if (!silent) {
      toast(state.lang === 'en' ? 'A4 Handout generated successfully!' : '隨堂講義已生成完畢！');
      switchView('deck');
      switchPreviewTab('handout');
    }
    return true;
  } catch (err) {
    updateModuleStatusChip(
      'handoutStatusChip',
      'error',
      state.lang === 'en' ? '✗ Handout generation failed' : '✗ 講義生成失敗'
    );
    await fetchCurrentUser();
    toast(err.message || (state.lang === 'en' ? 'Handout generation failed' : '講義生成失敗'), true);
    return false;
  } finally {
    setBtnLoading(btn, false);
    if (showOverlay) loading(false);
  }
}

// 3. 單元試卷 (Quiz) 生成 Action
async function generateQuizAction(silent = false, showOverlay = true) {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in first' : '請先登入帳號', true);
    openAuthModal('login');
    return false;
  }
  if (!state.document) {
    toast(state.lang === 'en' ? 'Please upload a material first' : '請先上傳教材', true);
    return false;
  }

  const btn = $('#generateQuizBtn');
  setBtnLoading(btn, true);
  updateModuleStatusChip(
    'quizStatusChip',
    'running',
    state.lang === 'en' ? 'Generating quiz...' : '試卷生成中...'
  );

  const audience = $('#audience') ? $('#audience').value : '一般大眾/初學者';
  const tone = $('#tone') ? $('#tone').value : '清楚易懂';
  const language = $('#targetLanguage') ? $('#targetLanguage').value : 'auto';
  const question_count = +($('#quizCount')?.value || 5);
  const difficulty = $('#quizDifficulty')?.value || 'all';
  const enable_web_search = $('#quizWebSearch') ? $('#quizWebSearch').checked : false;
  const handoutText = getHandoutTextForContext();

  if (showOverlay) {
    const isEn = state.lang === 'en';
    loading(
      true,
      isEn ? 'Generating Unit Assessment & Quiz Sheet...' : '正在生成單元試卷評量…',
      isEn ? 'Planning question distribution and key concepts…' : `正在依據教材與【${tone}】風格規劃命題考點…`,
      isEn ? [
        `Setting question difficulty for ${audience}…`,
        `Crafting scenario questions with ${tone} style…`,
        'Formulating answer keys and distractor analyses…',
        'Writing step-by-step mathematical & physical solutions…',
        'Finalizing printable assessment sheet…'
      ] : [
        `針對【${audience}】調配題目難度與知識陷阱…`,
        `以【${tone}】設計生活情境與探究式題幹…`,
        '編撰標準答案與深入誘答項解析…',
        '撰寫詳細推導步驟與 LaTeX 數學算式…',
        '即將完成單元試卷評量…'
      ]
    );
  }

  try {
    const quiz = await api('/api/quiz/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: state.document.id,
        audience,
        tone,
        language,
        question_count,
        difficulty,
        enable_web_search,
        handout_text: handoutText || undefined,
      })
    });
    state.quiz = quiz;
    saveWorkspaceStateToStorage();
    updatePreviewCountBadge();
    await fetchCurrentUser();
    renderQuizPreview();

    updateModuleStatusChip(
      'quizStatusChip',
      'success',
      state.lang === 'en' ? '✓ Quiz Ready (Click to View)' : '✓ 試卷已就緒 (點擊查看)',
      () => { switchView('deck'); switchPreviewTab('quiz'); }
    );

    if (!silent) {
      toast(state.lang === 'en' ? 'Unit Quiz generated successfully!' : '單元試卷已出題完畢！');
      switchView('deck');
      switchPreviewTab('quiz');
    }
    return true;
  } catch (err) {
    updateModuleStatusChip(
      'quizStatusChip',
      'error',
      state.lang === 'en' ? '✗ Quiz generation failed' : '✗ 試卷生成失敗'
    );
    await fetchCurrentUser();
    toast(err.message || (state.lang === 'en' ? 'Quiz generation failed' : '試卷生成失敗'), true);
    return false;
  } finally {
    setBtnLoading(btn, false);
    if (showOverlay) loading(false);
  }
}

// 4. 一鍵全部生成 (方案 B：以講義為母本，串接簡報與試卷衍生)
async function generateAllAction() {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in first' : '請先登入帳號', true);
    openAuthModal('login');
    return;
  }
  if (!state.document) {
    toast(state.lang === 'en' ? 'Please upload a material first' : '請先上傳教材', true);
    return;
  }

  const allBtn = $('#generateAllBtn');
  setBtnLoading(allBtn, true);

  const tone = $('#tone') ? $('#tone').value : '清楚易懂';
  const audience = $('#audience') ? $('#audience').value : '一般大眾/初學者';
  const isEn = state.lang === 'en';

  loading(
    true,
    isEn ? 'Generating Complete Lesson Package...' : '正在一鍵生成全套教案…',
    isEn ? 'Step 1/2: Generating A4 Handout Master…' : '步驟 1/2：正在生成 A4 隨堂講義母本…',
    isEn ? [
      `Step 1/2: Crafting A4 Handout with ${tone} style for ${audience}…`,
      'Step 2/2: Deriving Slide Deck and Quiz in parallel…',
      'Writing speaker notes and comprehensive quiz explanations…',
      'Finalizing all 3 teaching materials in parallel…'
    ] : [
      `步驟 1/2：以【${tone}】風格為【${audience}】編撰 A4 隨堂講義母本…`,
      '步驟 2/2：依據講義母本並行生成教學簡報與單元試卷…',
      '撰寫逐頁演講稿與試卷詳細解析…',
      '即將完成講義、簡報、試卷全套教案…'
    ]
  );

  try {
    // 步驟 1：先生成 A4 隨堂講義作為母本 (showOverlay = false 由父層統一管理)
    const handoutSuccess = await generateHandoutAction(true, false);

    // 步驟 2：由講義母本並行衍生簡報與試卷 (雙軌融合，極低 Token 消耗)
    const results = await Promise.allSettled([
      generateDeckAction(true, false),
      generateQuizAction(true, false),
    ]);

    const deckSuccess = results[0].status === 'fulfilled' && results[0].value === true;
    const quizSuccess = results[1].status === 'fulfilled' && results[1].value === true;

    if (handoutSuccess && deckSuccess && quizSuccess) {
      toast(state.lang === 'en' ? 'All 3 modules generated successfully! Check in Outputs & Preview.' : '講義、簡報與試卷全套生成完畢！請至產出預覽查看。');
      switchView('deck');
      switchPreviewTab('handout');
    } else {
      const count = (handoutSuccess ? 1 : 0) + (deckSuccess ? 1 : 0) + (quizSuccess ? 1 : 0);
      toast(state.lang === 'en' ? `Generated ${count}/3 items. Check module statuses.` : `已完成 ${count}/3 項生成，請查看各模組狀態。`);
    }
  } finally {
    setBtnLoading(allBtn, false);
    loading(false);
  }
}

// 綁定獨立按鈕與一鍵生成按鈕
$('#generateHandoutBtn')?.addEventListener('click', () => generateHandoutAction());
$('#generateBtn')?.addEventListener('click', () => generateDeckAction());
$('#generateQuizBtn')?.addEventListener('click', () => generateQuizAction());
$('#generateAllBtn')?.addEventListener('click', () => generateAllAction());

// 綁定講義預覽連鎖觸發按鈕
$('#handoutToWorkbenchBtn')?.addEventListener('click', () => {
  switchView('workspace');
  const target = $('#deckModuleCard') || $('#settingsCard');
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

// === 產出預覽中心 Sub-tabs 切換與渲染 ===
let currentPreviewTab = 'handout';

function switchPreviewTab(tabName = 'handout') {
  currentPreviewTab = tabName;
  const tabs = ['handout', 'deck', 'quiz'];
  $$('.preview-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.previewTab === tabName);
  });
  tabs.forEach(t => {
    const panel = $(`#preview${t.charAt(0).toUpperCase() + t.slice(1)}Panel`);
    const actions = $(`#${t}DownloadActions`);
    if (panel) panel.classList.toggle('hidden', t !== tabName);
    if (actions) actions.classList.toggle('hidden', t !== tabName);
  });

  if (tabName === 'deck') renderDeck();
  if (tabName === 'handout') renderHandoutPreview();
  if (tabName === 'quiz') renderQuizPreview();
}

$$('.preview-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.previewTab;
    if (tab) switchPreviewTab(tab);
  });
});

function updatePreviewCountBadge() {
  const el = $('#deckCount');
  if (!el) return;
  let count = 0;
  if (state.deck) count++;
  if (state.handout) count++;
  if (state.quiz) count++;
  el.textContent = String(count);
}

function renderPreviewPanels() {
  switchPreviewTab(currentPreviewTab || 'handout');
  updatePreviewCountBadge();
}

let patchHandoutTimeout = null;
function syncHandoutEdits() {
  if (!state.handout) return;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  clearTimeout(patchHandoutTimeout);
  patchHandoutTimeout = setTimeout(async () => {
    try {
      await api(`/api/handouts/${state.handout.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: state.handout.title,
          subtitle: state.handout.subtitle,
          overview: state.handout.overview,
          sections: state.handout.sections,
          key_takeaways: state.handout.key_takeaways
        })
      });
      updateGlobalSyncStatus('saved');
    } catch (err) {
      console.warn('Handout sync failed:', err);
      updateGlobalSyncStatus('saved');
    }
  }, 500);
}

async function flushHandoutEdits() {
  if (!state.handout) return;
  clearTimeout(patchHandoutTimeout);
  patchHandoutTimeout = null;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  try {
    await api(`/api/handouts/${state.handout.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: state.handout.title,
        subtitle: state.handout.subtitle,
        overview: state.handout.overview,
        sections: state.handout.sections,
        key_takeaways: state.handout.key_takeaways
      })
    });
    updateGlobalSyncStatus('saved');
  } catch (err) {
    console.warn('Flush handout edits warning:', err);
    updateGlobalSyncStatus('saved');
  }
}

let patchQuizTimeout = null;
function syncQuizEdits() {
  if (!state.quiz) return;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  clearTimeout(patchQuizTimeout);
  patchQuizTimeout = setTimeout(async () => {
    try {
      await api(`/api/quiz/${state.quiz.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: state.quiz.title,
          description: state.quiz.description,
          questions: state.quiz.questions
        })
      });
      updateGlobalSyncStatus('saved');
    } catch (err) {
      console.warn('Quiz sync failed:', err);
      updateGlobalSyncStatus('saved');
    }
  }, 500);
}

async function flushQuizEdits() {
  if (!state.quiz) return;
  clearTimeout(patchQuizTimeout);
  patchQuizTimeout = null;
  saveWorkspaceStateToStorage();
  updateGlobalSyncStatus('saving');
  try {
    await api(`/api/quiz/${state.quiz.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: state.quiz.title,
        description: state.quiz.description,
        questions: state.quiz.questions
      })
    });
    updateGlobalSyncStatus('saved');
  } catch (err) {
    console.warn('Flush quiz edits warning:', err);
    updateGlobalSyncStatus('saved');
  }
}

// 講義匯出按鈕即時 Flush 攔截
$('#previewHandoutPrintBtn')?.addEventListener('click', async (e) => {
  if (!state.handout) return;
  e.preventDefault();
  await flushHandoutEdits();
  window.open(`/api/handouts/${state.handout.id}/print`, '_blank');
});
$('#previewHandoutDocxBtn')?.addEventListener('click', async (e) => {
  if (!state.handout) return;
  e.preventDefault();
  await flushHandoutEdits();
  window.location.href = `/api/handouts/${state.handout.id}/docx`;
});

// 試卷匯出按鈕即時 Flush 攔截
$('#previewQuizPrintBtn')?.addEventListener('click', async (e) => {
  if (!state.quiz) return;
  e.preventDefault();
  await flushQuizEdits();
  const showTeacher = $('#previewQuizTeacherToggle') ? $('#previewQuizTeacherToggle').checked : false;
  window.open(`/api/quiz/${state.quiz.id}/print?teacher=${showTeacher}`, '_blank');
});
$('#previewQuizDocxBtn')?.addEventListener('click', async (e) => {
  if (!state.quiz) return;
  e.preventDefault();
  await flushQuizEdits();
  const showTeacher = $('#previewQuizTeacherToggle') ? $('#previewQuizTeacherToggle').checked : false;
  window.location.href = `/api/quiz/${state.quiz.id}/docx?teacher=${showTeacher}`;
});

// 容器層事件代理：講義就地即時編輯
$('#previewHandoutContainer')?.addEventListener('input', (e) => {
  if (!state.handout) return;
  const h = state.handout;
  const target = e.target;

  if (target.id === 'handoutPreviewTitle' || target.closest('#handoutPreviewTitle')) {
    const el = target.id === 'handoutPreviewTitle' ? target : target.closest('#handoutPreviewTitle');
    h.title = el.innerText.trim();
    syncHandoutEdits();
    return;
  }
  if (target.id === 'handoutPreviewOverview' || target.closest('#handoutPreviewOverview')) {
    const el = target.id === 'handoutPreviewOverview' ? target : target.closest('#handoutPreviewOverview');
    h.overview = el.innerText;
    syncHandoutEdits();
    return;
  }
  const secTitle = target.closest('[data-h-sec-title]');
  if (secTitle) {
    const sIdx = parseInt(secTitle.dataset.hSecTitle, 10);
    if (h.sections && h.sections[sIdx]) h.sections[sIdx].title = secTitle.innerText.trim();
    syncHandoutEdits();
    return;
  }
  const secSum = target.closest('[data-h-sec-sum]');
  if (secSum) {
    const sIdx = parseInt(secSum.dataset.hSecSum, 10);
    if (h.sections && h.sections[sIdx]) {
      h.sections[sIdx].summary = secSum.innerText;
      h.sections[sIdx].core_concept = secSum.innerText;
    }
    syncHandoutEdits();
    return;
  }
  const secExp = target.closest('[data-h-sec-exp]');
  if (secExp) {
    const sIdx = parseInt(secExp.dataset.hSecExp, 10);
    if (h.sections && h.sections[sIdx]) h.sections[sIdx].detailed_explanation = secExp.innerText;
    syncHandoutEdits();
    return;
  }
  const secKp = target.closest('[data-h-sec-kp]');
  if (secKp) {
    const [sIdxStr, kIdxStr] = (secKp.dataset.hSecKp || '').split('_');
    const sIdx = parseInt(sIdxStr, 10);
    const kIdx = parseInt(kIdxStr, 10);
    if (h.sections && h.sections[sIdx]) {
      if (Array.isArray(h.sections[sIdx].key_points)) h.sections[sIdx].key_points[kIdx] = secKp.innerText;
      if (Array.isArray(h.sections[sIdx].key_takeaways)) h.sections[sIdx].key_takeaways[kIdx] = secKp.innerText;
    }
    syncHandoutEdits();
    return;
  }
  const secDq = target.closest('[data-h-sec-dq]');
  if (secDq) {
    const [sIdxStr, dqIdxStr] = (secDq.dataset.hSecDq || '').split('_');
    const sIdx = parseInt(sIdxStr, 10);
    const dqIdx = parseInt(dqIdxStr, 10);
    if (h.sections && h.sections[sIdx] && Array.isArray(h.sections[sIdx].discussion_questions)) {
      h.sections[sIdx].discussion_questions[dqIdx] = secDq.innerText;
    }
    syncHandoutEdits();
    return;
  }
  const takeaway = target.closest('[data-h-takeaway]');
  if (takeaway) {
    const tIdx = parseInt(takeaway.dataset.hTakeaway, 10);
    if (Array.isArray(h.key_takeaways)) h.key_takeaways[tIdx] = takeaway.innerText;
    syncHandoutEdits();
    return;
  }
});

// 容器層事件代理：試卷就地即時編輯
$('#previewQuizContainer')?.addEventListener('input', (e) => {
  if (!state.quiz) return;
  const q = state.quiz;
  const target = e.target;

  if (target.id === 'quizPreviewTitle' || target.closest('#quizPreviewTitle')) {
    const el = target.id === 'quizPreviewTitle' ? target : target.closest('#quizPreviewTitle');
    q.title = el.innerText.trim();
    syncQuizEdits();
    return;
  }
  const qText = target.closest('[data-q-text-idx]');
  if (qText) {
    const qIdx = parseInt(qText.dataset.qTextIdx, 10);
    if (q.questions && q.questions[qIdx]) q.questions[qIdx].question = qText.innerText.trim();
    syncQuizEdits();
    return;
  }
  const qOpt = target.closest('[data-q-opt-idx]');
  if (qOpt) {
    const [qIdxStr, optIdxStr] = (qOpt.dataset.qOptIdx || '').split('_');
    const qIdx = parseInt(qIdxStr, 10);
    const optIdx = parseInt(optIdxStr, 10);
    if (q.questions && q.questions[qIdx] && Array.isArray(q.questions[qIdx].options)) {
      q.questions[qIdx].options[optIdx] = qOpt.innerText;
    }
    syncQuizEdits();
    return;
  }
  const qAns = target.closest('[data-q-ans-idx]');
  if (qAns) {
    const qIdx = parseInt(qAns.dataset.qAnsIdx, 10);
    if (q.questions && q.questions[qIdx]) q.questions[qIdx].answer = qAns.innerText.trim();
    syncQuizEdits();
    return;
  }
  const qExp = target.closest('[data-q-exp-idx]');
  if (qExp) {
    const qIdx = parseInt(qExp.dataset.qExpIdx, 10);
    if (q.questions && q.questions[qIdx]) q.questions[qIdx].explanation = qExp.innerText;
    syncQuizEdits();
    return;
  }
});

async function regenerateSingleQuizQuestion(qIndex, targetBtn) {
  if (!state.quiz || !state.quiz.questions || !state.quiz.questions[qIndex]) return;
  const isEn = state.lang === 'en';
  if (targetBtn) {
    targetBtn.disabled = true;
    targetBtn.textContent = isEn ? '🔄 Replacing...' : '🔄 換題中...';
  }
  try {
    const res = await api(`/api/quiz/${state.quiz.id}/questions/${qIndex}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instruction: '抽換為同概念但不同情境題型之高品質新試題',
        current_question: state.quiz.questions[qIndex],
        quiz: state.quiz,
        difficulty: state.quiz.questions[qIndex].difficulty || 'medium',
        language: state.quiz.language || state.lang || 'zh-TW'
      })
    });
    if (res && res.question) {
      state.quiz.questions[qIndex] = res.question;
      renderQuizPreview();
      if ($('#quizModal') && !$('#quizModal').classList.contains('hidden')) {
        renderQuizModal(state.quiz);
      }
      toast(isEn ? '🔄 Question replaced with a fresh new item! (-3 pts)' : '🔄 題目已成功抽換為全新試題！(消耗 3 點)');
      await fetchCurrentUser();
    }
  } catch (err) {
    toast(err.message || (isEn ? 'Failed to replace question' : '抽換題目失敗'), true);
  } finally {
    if (targetBtn) {
      targetBtn.disabled = false;
      targetBtn.textContent = isEn ? '🔄 Replace (3 pts)' : '🔄 換這題 (3 點)';
    }
  }
}

function wrapBareLatex(text) {
  if (!text || typeof text !== 'string' || !text.includes('\\')) return text;
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g);
  const cmdPattern = /(\\(?:vec|frac|sqrt|alpha|beta|gamma|delta|Delta|lambda|Lambda|theta|Theta|omega|Omega|sigma|Sigma|pi|Pi|sum|int|partial|infty|times|cdot|approx|pm|le|ge|neq|equiv|rightarrow|leftarrow|mathbf|mathrm|text|left|right|quad)\b[^\n,，。！？；;]*?(?=[,，。！？；;\s]|$))/g;
  return parts.map((part, idx) => {
    if (idx % 2 === 1) return part;
    return part.replace(cmdPattern, (m) => {
      const s = m.trim();
      return s.startsWith('$') ? s : `$${s}$`;
    });
  }).join('');
}

function formatInlineMarkdown(text) {
  if (!text) return '';
  text = wrapBareLatex(String(text));
  const mathTokens = [];
  let processed = text.replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, (m) => {
    const ph = `%%INLINEMATH${mathTokens.length}%%`;
    mathTokens.push(m);
    return ph;
  });
  processed = escapeHtml(processed);
  processed = processed.replace(/\*\*([^\*\n]+?)\*\*/g, '<strong>$1</strong>');
  processed = processed.replace(/__([^_\n]+?)__/g, '<strong>$1</strong>');
  processed = processed.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g, '<em>$1</em>');
  processed = processed.replace(/`([^`\n]+?)`/g, '<code style="background:rgba(0,0,0,0.06);padding:2px 4px;border-radius:4px;font-family:monospace;">$1</code>');
  mathTokens.forEach((m, idx) => {
    processed = processed.replace(`%%INLINEMATH${idx}%%`, m);
  });
  return processed;
}

// 渲染 A4 講義預覽 (自然多色塊功能分區排版)
function renderHandoutPreview() {
  const container = $('#previewHandoutContainer');
  if (!container) return;
  const isEn = state.lang === 'en';

  if (!state.handout) {
    container.innerHTML = `
      <div class="preview-empty-state">
        <span>📝</span>
        <b>${isEn ? 'No Handout Generated Yet' : '尚未生成隨堂講義'}</b>
        <small>${isEn ? 'Click "Generate A4 Handout" in Workspace to create one.' : '請在工作台點擊「📝 生成 A4 隨堂講義」或「🚀 一鍵生成全套教案」'}</small>
        <button class="secondary-button" type="button" onclick="switchView('workspace')">${isEn ? '← Go to Workspace' : '← 前往工作台生成'}</button>
      </div>
    `;
    if ($('#handoutToWorkbenchBtn')) $('#handoutToWorkbenchBtn').classList.add('disabled');
    if ($('#previewHandoutPrintBtn')) $('#previewHandoutPrintBtn').classList.add('disabled');
    if ($('#previewHandoutDocxBtn')) $('#previewHandoutDocxBtn').classList.add('disabled');
    return;
  }

  const handout = state.handout;
  const toWorkbenchBtn = $('#handoutToWorkbenchBtn');
  if (toWorkbenchBtn) {
    toWorkbenchBtn.classList.remove('disabled');
    toWorkbenchBtn.onclick = () => {
      switchView('workspace');
      const target = $('#deckModuleCard') || $('#settingsCard');
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };
  }
  if ($('#previewHandoutPrintBtn')) {
    $('#previewHandoutPrintBtn').href = `/api/handouts/${handout.id}/print`;
    $('#previewHandoutPrintBtn').classList.remove('disabled');
  }
  if ($('#previewHandoutDocxBtn')) {
    $('#previewHandoutDocxBtn').href = `/api/handouts/${handout.id}/docx`;
    $('#previewHandoutDocxBtn').classList.remove('disabled');
  }

  let sectionsHtml = '';
  if (handout.sections && handout.sections.length) {
    sectionsHtml = handout.sections.map((s, idx) => `
      <div class="handout-section-card">
        <h3>§ ${idx + 1}. <span contenteditable="true" spellcheck="false" data-h-sec-title="${idx}" title="點擊直接修改章節標題">${formatInlineMarkdown(s.title)}</span></h3>
        <p class="sec-summary"><span contenteditable="true" spellcheck="false" data-h-sec-sum="${idx}" title="點擊直接修改導讀摘要">${formatInlineMarkdown(s.summary || s.core_concept || '')}</span></p>
        ${s.detailed_explanation ? `<p style="margin: 0 0 12px 0; color: #475569; font-size: 13.5px; line-height: 1.7;"><span contenteditable="true" spellcheck="false" data-h-sec-exp="${idx}" title="點擊直接修改說明">${formatInlineMarkdown(s.detailed_explanation)}</span></p>` : ''}
        ${(s.key_points && s.key_points.length) || (s.key_takeaways && s.key_takeaways.length) ? `
          <div class="handout-key-points-box">
            <b>${isEn ? '📌 Key Points:' : '📌 核心要點'}</b>
            <ul>
              ${(s.key_points || s.key_takeaways || []).map((k, kIdx) => `<li contenteditable="true" spellcheck="false" data-h-sec-kp="${idx}_${kIdx}">${formatInlineMarkdown(k)}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        ${s.discussion_questions && s.discussion_questions.length ? `
          <div class="handout-questions-box">
            <b>${isEn ? '💬 Practice & Discussion:' : '💬 隨堂思考與練習'}</b>
            <ol>
              ${s.discussion_questions.map((dq, dqIdx) => `<li contenteditable="true" spellcheck="false" data-h-sec-dq="${idx}_${dqIdx}">${formatInlineMarkdown(dq)}</li>`).join('')}
            </ol>
          </div>
        ` : ''}
        ${s.source_pages && s.source_pages.length ? `<small class="handout-source-pages">${isEn ? 'Source: Page ' : '教材出處：第 '}${s.source_pages.join(', ')}${isEn ? '' : ' 頁'}</small>` : ''}
      </div>
    `).join('');
  }

  container.innerHTML = `
    <div class="handout-header-block">
      <h2 contenteditable="true" spellcheck="false" id="handoutPreviewTitle" title="點擊直接修改標題">${formatInlineMarkdown(handout.title || (isEn ? 'Lesson Handout' : '隨堂講義'))}</h2>
      <p>${formatInlineMarkdown(handout.subtitle || '')} · ${isEn ? 'Target: ' : '適用對象：'}${escapeHtml(handout.target_audience || '')}</p>
    </div>
    ${handout.overview || handout.overall_summary ? `
      <div class="handout-overview-box">
        <b>${isEn ? '📖 Course Overview:' : '📖 課程導讀：'}</b>
        <span contenteditable="true" spellcheck="false" id="handoutPreviewOverview" title="點擊直接修改導讀">${formatInlineMarkdown(handout.overview || handout.overall_summary || '')}</span>
      </div>
    ` : ''}
    ${sectionsHtml}
    ${handout.key_takeaways && handout.key_takeaways.length ? `
      <div class="handout-takeaways-box">
        <b>${isEn ? '💡 Key Takeaways' : '💡 課後總結與精華 (Key Takeaways)'}</b>
        <ul>
          ${handout.key_takeaways.map((tip, tIdx) => `<li contenteditable="true" spellcheck="false" data-h-takeaway="${tIdx}">${formatInlineMarkdown(tip)}</li>`).join('')}
        </ul>
      </div>
    ` : ''}
  `;

  renderMath(container);
}

// 渲染單元試卷預覽 (靛藍灰色系)
function renderQuizPreview() {
  const container = $('#previewQuizContainer');
  if (!container) return;
  const isEn = state.lang === 'en';

  if (!state.quiz) {
    container.innerHTML = `
      <div class="preview-empty-state">
        <span>📑</span>
        <b style="color: #2c4a63;">${isEn ? 'No Quiz Sheet Generated Yet' : '尚未生成單元試卷'}</b>
        <small>${isEn ? 'Click "Generate Unit Quiz" in Workspace to create one.' : '請在工作台點擊「📑 生成單元試卷」或「🚀 一鍵生成全套教案」'}</small>
        <button class="secondary-button" style="color: #2c4a63; border-color: #cbd5e1; background: #f0f4f8;" type="button" onclick="switchView('workspace')">${isEn ? '← Go to Workspace' : '← 前往工作台生成'}</button>
      </div>
    `;
    if ($('#previewQuizPrintBtn')) $('#previewQuizPrintBtn').classList.add('disabled');
    if ($('#previewQuizDocxBtn')) $('#previewQuizDocxBtn').classList.add('disabled');
    return;
  }

  const quiz = state.quiz;
  const showTeacher = $('#previewQuizTeacherToggle') ? $('#previewQuizTeacherToggle').checked : false;
  if ($('#previewQuizPrintBtn')) {
    $('#previewQuizPrintBtn').href = `/api/quiz/${quiz.id}/print?teacher=${showTeacher}`;
    $('#previewQuizPrintBtn').classList.remove('disabled');
  }
  if ($('#previewQuizDocxBtn')) {
    $('#previewQuizDocxBtn').href = `/api/quiz/${quiz.id}/docx?teacher=${showTeacher}`;
    $('#previewQuizDocxBtn').classList.remove('disabled');
  }

  const diffLabels = {
    'easy': isEn ? 'Basic' : '基礎觀念',
    'medium': isEn ? 'Moderate' : '中等理解',
    'hard': isEn ? 'Advanced' : '進階論述'
  };

  container.innerHTML = `
    <div style="margin-bottom: 20px; padding-bottom: 14px; border-bottom: 2px solid #cbd5e1;">
      <h2 style="font-size: 22px; font-weight: 800; color: #2c4a63; margin: 0 0 6px 0;" contenteditable="true" spellcheck="false" id="quizPreviewTitle" title="點擊直接修改標題">${formatInlineMarkdown(quiz.title || (isEn ? 'Unit Quiz' : '單元試卷'))}</h2>
      <p style="margin: 0; color: #64748b; font-size: 13px;">${formatInlineMarkdown(quiz.description || '')} · ${quiz.questions ? quiz.questions.length : 0} ${isEn ? 'Questions' : '題'}</p>
    </div>
    ${(quiz.questions || []).map((q, idx) => `
      <div class="quiz-question-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 8px;">
          <h4>
            第 ${idx + 1} 題. <span contenteditable="true" spellcheck="false" data-q-text-idx="${idx}" title="點擊直接修改題目內容">${formatInlineMarkdown(q.question)}</span>
          </h4>
          <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
            <button type="button" class="btn-regen-question" data-qidx="${idx}" title="消耗 3 點備課點數抽換此題">🔄 換這題 (3 點)</button>
            <span class="quiz-diff-chip">
              ${diffLabels[q.difficulty] || q.difficulty}
            </span>
          </div>
        </div>
        <div style="margin: 10px 0 12px 10px; display: grid; grid-template-columns: 1fr; gap: 8px;">
          ${(q.options || []).map((opt, optIdx) => `
            <div class="quiz-option-item" contenteditable="true" spellcheck="false" data-q-opt-idx="${idx}_${optIdx}" title="點擊直接修改選項">
              ${formatInlineMarkdown(opt)}
            </div>
          `).join('')}
        </div>
        <div class="preview-quiz-ans-block ${showTeacher ? '' : 'hidden'}">
          <p style="margin: 0 0 4px 0; font-weight: 700; color: #2c4a63;">${isEn ? 'Answer: ' : '【標準答案】'} <span contenteditable="true" spellcheck="false" data-q-ans-idx="${idx}">${formatInlineMarkdown(q.answer)}</span></p>
          <p style="margin: 0; color: #334155;"><b>${isEn ? 'Explanation: ' : '【解析】'}</b><span contenteditable="true" spellcheck="false" data-q-exp-idx="${idx}" title="點擊直接修改解析">${formatInlineMarkdown(q.explanation)}</span></p>
          ${q.source_pages && q.source_pages.length ? `<small style="display: block; margin-top: 6px; color: #94a3b8;">${isEn ? 'Source Page: ' : '教材依據：第 '}${q.source_pages.join(', ')}${isEn ? '' : ' 頁'}</small>` : ''}
        </div>
      </div>
    `).join('')}
  `;

  // 綁定抽換題目事件
  $$('.btn-regen-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const qIdx = parseInt(btn.dataset.qidx, 10);
      regenerateSingleQuizQuestion(qIdx, btn);
    });
  });

  renderMath(container);
}

$('#previewQuizTeacherToggle')?.addEventListener('change', () => {
  const isChecked = $('#previewQuizTeacherToggle').checked;
  $$('.preview-quiz-ans-block').forEach(el => el.classList.toggle('hidden', !isChecked));
  if (state.quiz) {
    if ($('#previewQuizPrintBtn')) {
      $('#previewQuizPrintBtn').href = `/api/quiz/${state.quiz.id}/print?teacher=${isChecked}`;
    }
    if ($('#previewQuizDocxBtn')) {
      $('#previewQuizDocxBtn').href = `/api/quiz/${state.quiz.id}/docx?teacher=${isChecked}`;
    }
  }
});

// === 隨堂講義 Modal 渲染與關閉 ===
function renderHandoutModal(handout) {
  if (!handout) return;
  const isEn = state.lang === 'en';
  if ($('#handoutModalTitle')) $('#handoutModalTitle').textContent = handout.title || (isEn ? 'Lesson Handout' : '隨堂講義');
  if ($('#handoutModalSubtitle')) $('#handoutModalSubtitle').textContent = `${handout.subtitle || ''} · ${isEn ? 'Target: ' : '適用對象：'}${handout.target_audience || ''}`;

  const bodyEl = $('#handoutModalBody');
  if (bodyEl) {
    let sectionsHtml = '';
    if (handout.sections && handout.sections.length) {
      sectionsHtml = handout.sections.map((s, idx) => `
        <div class="handout-section-card" style="margin-bottom: 20px; padding: 14px; background: #f8fafc; border-radius: 8px; border-left: 4px solid #2563eb;">
          <h3 style="font-size: 16px; font-weight: 700; color: #1e3a8a; margin: 0 0 8px 0;">§ ${idx + 1}. ${escapeHtml(s.title)}</h3>
          <p style="margin: 0 0 6px 0; color: #334155;"><b>${isEn ? 'Core Concept: ' : '✦ 核心概念：'}</b>${escapeHtml(s.core_concept)}</p>
          <p style="margin: 0 0 10px 0; color: #475569; font-size: 13px; line-height: 1.6;">${escapeHtml(s.detailed_explanation)}</p>
          ${s.key_takeaways && s.key_takeaways.length ? `
            <div style="background: #eff6ff; padding: 8px 12px; border-radius: 6px; font-size: 13px; color: #1e40af;">
              <b>${isEn ? 'Key Takeaways:' : '📌 重點整理：'}</b>
              <ul style="margin: 4px 0 0 16px; padding: 0;">
                ${s.key_takeaways.map(k => `<li>${escapeHtml(k)}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          ${s.source_pages && s.source_pages.length ? `<small style="display: block; margin-top: 6px; color: #94a3b8;">${isEn ? 'Source Page: ' : '教材頁碼：'}${s.source_pages.join(', ')}</small>` : ''}
        </div>
      `).join('');
    }

    bodyEl.innerHTML = `
      ${handout.overall_summary ? `
        <div style="margin-bottom: 16px; padding: 12px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0; color: #166534;">
          <b>${isEn ? 'Course Summary: ' : '課程整體導讀：'}</b>
          <p style="margin: 4px 0 0 0; font-size: 13px;">${escapeHtml(handout.overall_summary)}</p>
        </div>
      ` : ''}
      ${sectionsHtml}
      ${handout.study_tips && handout.study_tips.length ? `
        <div style="margin-top: 16px; padding: 12px; background: #fffbeb; border-radius: 8px; border: 1px solid #fde68a; color: #92400e;">
          <b>${isEn ? 'Study Tips: ' : '研讀建議與復習指南：'}</b>
          <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 13px;">
            ${handout.study_tips.map(tip => `<li>${escapeHtml(tip)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    `;

    renderMath(bodyEl);
  }

  // 綁定匯出連結
  if ($('#handoutPrintBtn')) $('#handoutPrintBtn').href = `/api/handouts/${handout.id}/html`;
  if ($('#handoutDownloadMdBtn')) $('#handoutDownloadMdBtn').href = `/api/handouts/${handout.id}/markdown`;

  const modal = $('#handoutModal');
  if (modal) modal.classList.remove('hidden');
}

function closeHandoutModal() {
  const modal = $('#handoutModal');
  if (modal) modal.classList.add('hidden');
}
$('#closeHandoutModalBtn')?.addEventListener('click', closeHandoutModal);
$('#handoutModal')?.addEventListener('click', (e) => {
  if (e.target === $('#handoutModal')) closeHandoutModal();
});

// === 單元試卷 Modal 渲染與關閉 ===
function renderQuizModal(quiz) {
  quiz = quiz || state.quiz;
  if (!quiz) return;
  const isEn = state.lang === 'en';
  if ($('#quizModalTitle')) $('#quizModalTitle').textContent = quiz.title || (isEn ? 'Unit Quiz' : '單元試卷');
  if ($('#quizModalSubtitle')) $('#quizModalSubtitle').textContent = `${quiz.description || ''} · ${quiz.questions ? quiz.questions.length : 0} ${isEn ? 'Questions' : '題'}`;

  const bodyEl = $('#quizModalBody');
  const showTeacher = $('#quizTeacherModeToggle') ? $('#quizTeacherModeToggle').checked : false;

  if (bodyEl && quiz.questions) {
    const diffLabels = {
      'easy': isEn ? 'Basic' : '基礎觀念',
      'medium': isEn ? 'Moderate' : '中等理解',
      'hard': isEn ? 'Advanced' : '進階論述'
    };

    bodyEl.innerHTML = quiz.questions.map((q, idx) => `
      <div class="quiz-question-card" style="margin-bottom: 20px; padding: 16px; background: #ffffff; border-radius: 8px; border: 1px solid var(--line); border-left: 4px solid var(--green);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; gap: 8px;">
          <h4 style="font-size: 15px; font-weight: 700; color: var(--green); margin: 0; flex: 1;">第 ${idx + 1} 題. ${escapeHtml(q.question)}</h4>
          <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
            <button type="button" class="btn-regen-question modal-regen-btn" data-qidx="${idx}" title="消耗 3 點備課點數抽換此題">🔄 ${isEn ? 'Replace (3 pts)' : '換這題 (3 點)'}</button>
            <span style="font-size: 11px; padding: 2px 8px; border-radius: 99px; background: #ecefe8; color: var(--green); border: 1px solid #dce1d9; font-weight: 600; white-space: nowrap;">
              ${diffLabels[q.difficulty] || q.difficulty}
            </span>
          </div>
        </div>
        <div style="margin: 8px 0 10px 12px; display: grid; grid-template-columns: 1fr; gap: 6px;">
          ${(q.options || []).map(opt => `
            <div style="font-size: 13px; color: var(--ink); padding: 6px 10px; background: var(--card); border: 1px solid var(--line); border-radius: 6px;">
              ${escapeHtml(opt)}
            </div>
          `).join('')}
        </div>
        <div class="quiz-answer-block ${showTeacher ? '' : 'hidden'}" style="margin-top: 10px; padding: 10px 12px; background: #f4f7f4; border-radius: 6px; border: 1px solid #d1ded6; font-size: 13px; color: var(--green);">
          <p style="margin: 0 0 4px 0; font-weight: 700;">${isEn ? 'Answer: ' : '【標準答案】'} ${escapeHtml(q.answer)}</p>
          <p style="margin: 0; color: #2d5a4e;"><b>${isEn ? 'Explanation: ' : '【解析】'}</b>${escapeHtml(q.explanation)}</p>
          ${q.source_pages && q.source_pages.length ? `<small style="display: block; margin-top: 4px; color: var(--muted);">${isEn ? 'Source Page: ' : '教材依據：第 '}${q.source_pages.join(', ')}${isEn ? '' : ' 頁'}</small>` : ''}
        </div>
      </div>
    `).join('');

    bodyEl.querySelectorAll('.modal-regen-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const qIdx = parseInt(btn.dataset.qidx, 10);
        regenerateSingleQuizQuestion(qIdx, btn);
      });
    });

    renderMath(bodyEl);
  }

  // 綁定下載按鈕
  if ($('#quizDownloadStudentBtn')) $('#quizDownloadStudentBtn').href = `/api/quiz/${quiz.id}/markdown?teacher=false`;
  if ($('#quizDownloadTeacherBtn')) $('#quizDownloadTeacherBtn').href = `/api/quiz/${quiz.id}/markdown?teacher=true`;

  const modal = $('#quizModal');
  if (modal) modal.classList.remove('hidden');
}

$('#quizTeacherModeToggle')?.addEventListener('change', () => {
  const isChecked = $('#quizTeacherModeToggle').checked;
  $$('.quiz-answer-block').forEach(el => el.classList.toggle('hidden', !isChecked));
});

function closeQuizModal() {
  const modal = $('#quizModal');
  if (modal) modal.classList.add('hidden');
}
$('#closeQuizModalBtn')?.addEventListener('click', closeQuizModal);
$('#quizModal')?.addEventListener('click', (e) => {
  if (e.target === $('#quizModal')) closeQuizModal();
});

// 服務條款與隱私權政策 Modal 控制
function openTermsModal() {
  const modal = $('#termsModal');
  if (modal) modal.classList.remove('hidden');
}

function closeTermsModal() {
  const modal = $('#termsModal');
  if (modal) modal.classList.add('hidden');
}

function openPrivacyModal() {
  const modal = $('#privacyModal');
  if (modal) modal.classList.remove('hidden');
}

function closePrivacyModal() {
  const modal = $('#privacyModal');
  if (modal) modal.classList.add('hidden');
}

$('#openTermsBtn')?.addEventListener('click', openTermsModal);
$('#closeTermsModalBtn')?.addEventListener('click', closeTermsModal);
$('#confirmTermsBtn')?.addEventListener('click', closeTermsModal);
$('#termsModal')?.addEventListener('click', (e) => {
  if (e.target === $('#termsModal')) closeTermsModal();
});

$('#openPrivacyBtn')?.addEventListener('click', openPrivacyModal);
$('#closePrivacyModalBtn')?.addEventListener('click', closePrivacyModal);
$('#confirmPrivacyBtn')?.addEventListener('click', closePrivacyModal);
$('#privacyModal')?.addEventListener('click', (e) => {
  if (e.target === $('#privacyModal')) closePrivacyModal();
});

// 全域 ESC 鍵快速關閉所有 Modal
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    closeAuthModal();
    if (typeof closeCreateUserModal === 'function') closeCreateUserModal();
    if (typeof closeHandoutModal === 'function') closeHandoutModal();
    if (typeof closeQuizModal === 'function') closeQuizModal();
    if (typeof closeTermsModal === 'function') closeTermsModal();
    if (typeof closePrivacyModal === 'function') closePrivacyModal();
  }
});

// === 示範教材快速載入處理 (Demo Sample Loader) ===
const DEMO_SAMPLE_PHYSICS = `# 高中物理：牛頓運動定律與萬有引力定律

## 單元一：牛頓第一運動定律（慣性定律）
任何物體在不受外力作用，或所受合力為零的狀態下，靜者恆靜，動者恆作等速度直線運動。
這種維持原有運動狀態的性質稱為「慣性」。物體的質量即為其慣性大小的量度，質量愈大，其運動狀態愈難改變。
日常實例包括：急煞車時乘客向前傾斜、拍打衣服掃除灰塵等。

## 單元二：牛頓第二運動定律（運動定律）
當物體受外力作用時，將在力的方向上產生加速度。加速度的大小與作用力成正比，與物體的質量成反比。
數學表達式為：
$$ \\vec{F} = m \\vec{a} $$
其中力以牛頓（N）為單位，質量以公斤（kg）為單位，加速度以公尺每秒平方（m/s²）為單位。

## 單元三：牛頓第三運動定律（作用力與反作用力定律）
當兩物體相互作用時，施力物所施加的作用力與受力物所施加的反作用力，大小相等、方向相反，且同時發生於同一直線上，但分別作用於不同的物體上，因此不能互相抵消。
例如火箭推進、游泳划水等。

## 單元四：萬有引力定律
宇宙間任何兩個質點之間皆存在相互吸引的重力，其大小與兩質點質量的乘積成正比，與兩者距離的平方成反比：
$$ F_g = G \\frac{m_1 m_2}{r^2} $$
其中 $G = 6.674 \\times 10^{-11} \\, \\text{N}\\cdot\\text{m}^2/\\text{kg}^2$ 為萬有引力常數。重力為長程力，主導了天體運行與潮汐現象。`;

$('#loadSampleBtn')?.addEventListener('click', async () => {
  if (!state.user) {
    toast(state.lang === 'en' ? 'Please log in to use demo lesson' : '請先登入帳號以載入示範教材', true);
    openAuthModal('login');
    return;
  }
  loading(
    true,
    state.lang === 'en' ? 'Loading Sample Lesson...' : '正在載入示範教材…',
    state.lang === 'en' ? 'Indexing Newton Laws & Gravitation...' : '解析章節結構與建立向量索引…'
  );
  try {
    const doc = await api('/api/documents/import_text', {
      method: 'POST',
      body: JSON.stringify({
        title: state.lang === 'en' ? 'High_School_Physics_Newton_Laws.md' : '高中物理_牛頓運動定律與萬有引力.md',
        content: DEMO_SAMPLE_PHYSICS
      })
    });
    setDocument(doc);
    toast(state.lang === 'en' ? 'Sample lesson loaded successfully! Ready to generate.' : '示範教材載入成功！可以開始生成簡報、講義與試卷。');
  } catch (err) {
    toast(err.message, true);
  } finally {
    loading(false);
  }
});



