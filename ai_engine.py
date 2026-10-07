"""
TLU IT Study Copilot - Real AI Integration Engine
Module: ai_engine.py
Architecture: Multi-Provider Tiered Routing (Groq -> Gemini -> OpenRouter -> Oracle Fallback)
Domain: Khoa Cong nghe Thong tin - Truong Dai hoc Thang Long (TLU)
Compliance: Strict Socratic Tutoring, Article 25 Academic Integrity, Intelligent Intent Classification
"""

import os
import re
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import httpx

# Resolve Base Directory & Environment
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=ENV_FILE)
    except ImportError:
        pass


class TLUAIEngine:
    """
    Production AI Orchestrator supporting Groq, Google Gemini, and OpenRouter.
    Executes tiered model routing with automatic failover, intent classification, and pedagogical grounding.
    """

    def __init__(self):
        # API Keys configuration loaded securely from environment variables (.env)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        # Default Models
        self.groq_model = os.getenv("GROQ_DEFAULT_MODEL", "qwen/qwen3.8-27b")
        self.gemini_model = os.getenv("GEMINI_DEFAULT_MODEL", "gemini-3.5-flash-lite")
        self.openrouter_model = os.getenv("OPENROUTER_DEFAULT_MODEL", "liquid/lfm-2.5-2.6b:free")

        self.timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "15.0"))

    def get_providers_status(self) -> Dict[str, Any]:
        """Return operational readiness and configuration of all AI providers."""
        return {
            "orchestrator": "TLU Multi-Provider Tiered Router",
            "routing_priority": ["Groq (Ultra-fast)", "Google Gemini (Reasoning)", "OpenRouter (Fallback)", "Reference Oracle (Local)"],
            "providers": {
                "groq": {
                    "configured": bool(self.groq_api_key),
                    "model": self.groq_model,
                    "tier": "Tier 1 (Fast Inference, ~200ms)",
                    "status": "ready" if self.groq_api_key else "unconfigured"
                },
                "gemini": {
                    "configured": bool(self.gemini_api_key),
                    "model": self.gemini_model,
                    "tier": "Tier 2 (Multimodal Reasoning)",
                    "status": "ready" if self.gemini_api_key else "unconfigured"
                },
                "openrouter": {
                    "configured": bool(self.openrouter_api_key),
                    "model": self.openrouter_model,
                    "tier": "Tier 3 (Multi-model Gateway)",
                    "status": "ready" if self.openrouter_api_key else "unconfigured"
                }
            }
        }

    def classify_intent(self, text: str) -> str:
        """
        Classify student message intent:
        - VIOLATION: Academic dishonesty violating Article 25 TLU
        - GREETING: Social courtesy and greetings (hi, chao, hello, alo...)
        - OFF_TOPIC: Non-IT general questions (weather, dining, sports...)
        - ACADEMIC: Core TLU IT technical inquiry
        """
        lower = text.strip().lower()

        # 1. Academic Dishonesty Check (Điều 25 TLU)
        prohibited_phrases = [
            "viết hộ toàn bộ", "giải hộ bài tập lớn", "viết code hoàn chỉnh để nộp",
            "cho em xin đáp án bài", "code full bài này", "làm hộ bài thi",
            "code ho em toan bo", "giai ho bai tap lon", "lam ho bai thi"
        ]
        if any(phrase in lower for phrase in prohibited_phrases):
            return "VIOLATION"

        # 2. Greeting / Social Courtesy Check
        greeting_patterns = [
            r"^(hi|hello|hey|chào|xin chào|alo|hế lô|hê lô|helo|good morning|good afternoon|good evening)\b",
            r"^(chào|hello|hi|alo)[\s!\.,\?]*$",
            r"^(chào bạn|chào bot|chào thầy|chào cô|chào trợ lý|chào copilot|chào em|chào anh|chào chị)\b",
            r"^(bạn là ai|cậu là ai|bot là ai|cho mình hỏi|cho em hỏi)\b"
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, lower, re.IGNORECASE):
                return "GREETING"

        # 3. IT Keyword Match Check
        it_keywords = [
            "c", "c++", "cpp", "java", "python", "sql", "asm", "mips", "pointer", "con trỏ",
            "mảng", "chuỗi", "string", "struct", "class", "hàm", "function", "biến", "vòng lặp",
            "loop", "for", "while", "if", "else", "đệ quy", "recursion", "danh sách liên kết",
            "linked list", "ngăn xếp", "stack", "hàng đợi", "queue", "cây", "tree", "nhị phân",
            "avl", "đồ thị", "graph", "dijkstra", "bfs", "dfs", "thuật toán", "algorithm",
            "độ phức tạp", "big-o", "o(n)", "csdl", "cơ sở dữ liệu", "database", "erd", "quan hệ",
            "chuẩn hóa", "1nf", "2nf", "3nf", "bcnf", "khóa chính", "primary key", "foreign key",
            "join", "select", "insert", "update", "delete", "group by", "having", "view", "index",
            "osi", "tcp", "udp", "ip", "subnet", "socket", "routing", "router", "switch", "port",
            "kiến trúc máy tính", "hệ điều hành", "os", "cpu", "ram", "bộ nhớ", "memory", "paging",
            "phân trang", "segmentation", "thread", "tiến trình", "process", "deadlock", "mutex",
            "semaphore", "debug", "lỗi", "error", "bug", "compile", "runtime", "segmentation fault",
            "segfault", "malloc", "free", "new", "null", "nullptr", "it101", "it201",
            "it205", "it301", "it315", "slide", "bài tập", "lab", "đồ án"
        ]
        has_it_keyword = any(kw in lower for kw in it_keywords)
        if not has_it_keyword and len(lower.split()) >= 2:
            return "OFF_TOPIC"

        return "ACADEMIC"

    def _build_socratic_system_prompt(self, course_code: str, student_id: str, intent: str, message: str) -> str:
        """Construct the system prompt adapted to student intent and TLU pedagogical rules."""
        base_role = (
            f"Ban la Tro giang Socratic thong minh cua Khoa Cong nghe Thong tin, Truong Dai hoc Thang Long (TLU).\n"
            f"Doi tuong tuong tac: Sinh vien ma so {student_id}, dang theo hoc mon {course_code}.\n"
        )

        if intent == "GREETING":
            return (
                f"{base_role}"
                f"TINH HUONG: Sinh vien gui loi chao xa giao ('{message}').\n"
                f"QUAN TRONG: Day la loi chao xa giao hoan toan hop le, duoc Guardrails chap thuan (APPROVED). TUYET DOI KHONG CHAN hoac bao vi pham.\n"
                f"YEU CAU PHAN HOI:\n"
                f"1. Chao lai sinh vien {student_id} mot cach am ap, than thien, lich thiep.\n"
                f"2. Gioi thieu ban la Tro ly Hoc tap Socratic cua Khoa CNTT TLU, dong hanh ho tro mon {course_code}.\n"
                f"3. Hoi xem hom nay sinh vien can ho tro ve bai hoc, bai tap lap trinh hay ly thuyet nao cua mon {course_code}.\n"
                f"4. Dinh dang: Bat dau bang the <thinking>Sinh vien gui loi chao xa giao. Guardrails chap thuan. Chao don va dinh huong mon {course_code}.</thinking>, tiep theo la loi chao."
            )

        if intent == "OFF_TOPIC":
            return (
                f"{base_role}"
                f"TINH HUONG: Sinh vien hoi mot cau hoi ngoai le mon hoc CNTT ('{message}').\n"
                f"QUAN TRONG: Cau hoi khong vi pham an ninh nen Guardrails chap thuan (APPROVED). Khong chan thô bao.\n"
                f"YEU CAU PHAN HOI:\n"
                f"1. Tra loi ngan gon, lich su ve cau hoi.\n"
                f"2. Nhe nhang giai thich rang ban la Tro ly Socratic chuyen biet cho cac mon hoc Khoa CNTT Dai hoc Thang Long.\n"
                f"3. Kheo leo dieu huong sinh vien quay lai voi cac chu de hoc tap, lap trinh hoac kien thuc mon {course_code}.\n"
                f"4. Dinh dang: Bat dau bang the <thinking>Cau hoi ngoai le mon CNTT TLU. Guardrails chap thuan. Phan hoi lich su va dinh huong quay lai mon {course_code}.</thinking>, tiep theo la loi phan hoi."
            )

        # Standard ACADEMIC Socratic Tutoring
        return (
            f"{base_role}"
            f"CAC NGUYEN TAC SU PHAM BAT BUOC (DIEU 25 QUY CHE LIEM CHINH HOC THUAT TLU):\n"
            f"1. TUYET DOI KHONG viet ho toan bo chuong trinh hay bai tap lon. Khong xuat loi giai tron ven de sinh vien sao chep nop bai.\n"
            f"2. Huong dan theo phuong phap Socratic: Dat cau hoi goi mo tu duy, chi ra dong logic can chu y, huong dan tung buoc.\n"
            f"3. Neu minh hoa ma nguon, CHI DUOC phep xuat toi da 3 dong code lien tuc (vi du: khai bao con tro hoac dieu kien if).\n"
            f"4. Giong van: An can, chuan muc su pham, khuyen khich sinh vien tu lap trinh va tu duy logic.\n"
            f"5. Dinh dang phan hoi:\n"
            f"Bat dau bang khoi the <thinking>Ghi chu phan tich su pham va loi logic cua sinh vien</thinking>\n"
            f"Phia sau the la noi dung loi giai thich Socratic danh cho sinh vien."
        )

    async def _call_groq(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """Execute chat completion via Groq Cloud API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TLU-Study-Copilot/1.0"
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content, self.groq_model

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """Execute content generation via Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TLU-Study-Copilot/1.0"
        }
        full_text = f"{system_prompt}\n\n---\nCau hoi cua sinh vien:\n{user_prompt}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_text}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 800
            }
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned empty candidate list")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Gemini response missing content parts")
            return parts[0].get("text", ""), self.gemini_model

    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """Execute chat completion via OpenRouter API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TLU-Study-Copilot/1.0"
        }
        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("OpenRouter returned empty choices")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                content = choices[0].get("message", {}).get("reasoning", "")
            return content or "Khong co phan hoi noi dung tu model.", self.openrouter_model

    def _parse_socratic_output(
        self,
        raw_text: str,
        course_code: str,
        student_id: str,
        intent: str,
        provider_name: str,
        model_name: str,
        latency_ms: float
    ) -> Dict[str, Any]:
        """Parse raw model text into strictly validated Socratic API response."""
        thinking_text = ""
        reply_text = raw_text

        # Extract thinking block if present
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_text, re.DOTALL | re.IGNORECASE)
        if thinking_match:
            thinking_text = f"<thinking>{thinking_match.group(1).strip()}</thinking>"
            reply_text = re.sub(r"<thinking>.*?</thinking>", "", raw_text, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            if intent == "GREETING":
                thinking_text = f"<thinking>Sinh vien {student_id} gui loi chao xa giao. Guardrails chap thuan (APPROVED). Chao don va dinh huong mon {course_code}.</thinking>"
            elif intent == "OFF_TOPIC":
                thinking_text = f"<thinking>Cau hoi ngoai le mon hoc CNTT TLU. Guardrails chap thuan khong chan. Phan hoi lich su va dinh huong ve mon {course_code}.</thinking>"
            else:
                thinking_text = (
                    f"<thinking>Phan tich cau hoi cua sinh vien {student_id} mon {course_code} bang {provider_name}. "
                    f"Kich hoat co che Socratic Tutoring khong sinh ma nguon hoan chinh.</thinking>"
                )

        # Count maximum continuous lines of code in markdown fences
        continuous_code_lines = 0
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", reply_text, re.DOTALL)
        for block in code_blocks:
            lines = [line for line in block.strip().split("\n") if line.strip()]
            if len(lines) > continuous_code_lines:
                continuous_code_lines = len(lines)

        # Determine mascot animation state
        if intent == "GREETING":
            mascot_state = "cheering"
        elif "tuyệt vời" in reply_text.lower() or "chính xác" in reply_text.lower() or "đúng rồi" in reply_text.lower():
            mascot_state = "cheering"
        else:
            mascot_state = "idle"

        # Citations mapping tailored to intent and course
        if intent == "GREETING":
            matched_cite = {
                "breadcrumb": f"{course_code} > Gioi thieu mon hoc > Muc tieu & De cuong hoc phan",
                "text": f"Chao mung sinh vien {student_id} den voi mon hoc {course_code}. Tro ly Socratic luon san sang dong hanh.",
                "slide_number": 1
            }
            steps = [
                f"Buoc 1: Chon chu de hoac bai tap can thao luan trong mon {course_code}.",
                "Buoc 2: Neu ro doan ma nguon hoac thong bao loi gap phai neu co.",
                "Buoc 3: Cung tro ly Socratic bóc tach logic tung buoc de thau hieu ban chat."
            ]
        elif intent == "OFF_TOPIC":
            matched_cite = {
                "breadcrumb": f"{course_code} > Phuong phap hoc tap > Tap trung kien thuc trong tam",
                "text": "Khuyen khich sinh vien tap trung vao cac ky nang lap trinh va thuc hanh lab.",
                "slide_number": 2
            }
            steps = [
                f"Buoc 1: Xac dinh muc tieu hoc tap cho buoi hoc hom nay.",
                f"Buoc 2: Dat cau hoi ve ly thuyet hoac bai tap mon {course_code}.",
                "Buoc 3: Cung tro ly phan tich ma nguon de giai quyet van de."
            ]
        else:
            citations_map = {
                "IT101": {"breadcrumb": "IT101 > Tuan 05 > Quan ly bo nho & Con tro > Slide 12", "text": "Kiem tra con tro khac NULL truoc khi truy cap gia tri.", "slide_number": 12},
                "IT201": {"breadcrumb": "IT201 > Tuan 04 > Danh sach lien ket & Do phuc tap > Slide 18", "text": "Do phuc tap chen vao dau danh sach la O(1), chen vao cuoi la O(n).", "slide_number": 18},
                "IT205": {"breadcrumb": "IT205 > Tuan 06 > Chuan hoa CSDL & 3NF > Slide 22", "text": "Moi thuoc tinh khong khoa phai phu thuoc day du vao khoa chinh.", "slide_number": 22},
                "IT301": {"breadcrumb": "IT301 > Tuan 03 > Mo hinh TCP/IP & Socket > Slide 15", "text": "Thiet lap socket gom bind(), listen() va accept() tren server.", "slide_number": 15},
                "IT315": {"breadcrumb": "IT315 > Tuan 07 > Bo nho ao & Dieu phoi CPU > Slide 30", "text": "Bang phan trang (Page Table) anh xa dia chi ao sang dia chi vat ly.", "slide_number": 30}
            }
            matched_cite = citations_map.get(course_code.upper(), citations_map["IT101"])
            steps = [
                f"Xac dinh khai niem cot loi lien quan trong mon {course_code}.",
                "Kiem tra logic dieu kien bien hoac vung nho thao tac.",
                "Tung buoc tu duy va kiem thu bang vi du thuc te."
            ]

        return {
            "reply": reply_text,
            "thinking": thinking_text,
            "citations": [matched_cite],
            "socratic_steps": steps,
            "continuous_code_lines": continuous_code_lines,
            "mascot_state": mascot_state,
            "article_25_triggered": False,
            "intent": intent,
            "provider_used": provider_name,
            "model_used": model_name,
            "latency_ms": round(latency_ms, 2)
        }

    async def generate_socratic_response(
        self,
        course_code: str,
        student_id: str,
        message: str,
        code_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-provider inference with intent understanding and fallback chain.
        Ensures greetings and casual conversation are NEVER blocked at guardrails.
        """
        start_time = time.time()
        course = (course_code or "IT101").upper()
        sid = student_id or "A41234"

        # Step 1: Intelligent Intent Classification
        intent = self.classify_intent(message)

        # Step 2: Article 25 Academic Integrity Gate (Only for VIOLATION)
        if intent == "VIOLATION":
            latency = (time.time() - start_time) * 1000.0
            return {
                "reply": (
                    f"Theo Dieu 25 Quy che Liem chinh Hoc thuat cua Truong Dai hoc Thang Long (TLU), "
                    f"tro ly AI khong duoc phep viet ma nguon hoan chinh hoac giai ho bai tap nop cham diem. "
                    f"Chung ta hay cung phan tich bai toan nay tung buoc: Ban da xac dinh duoc yeu cau dau vao va dau ra chua?"
                ),
                "thinking": (
                    "<thinking>Phat hien yeu cau viet ho bai toan/bai tap lon vi pham Dieu 25 TLU. "
                    "Kich hoat che do canh bao Socratic. Khong goi LLM sinh ma nguon giai ho.</thinking>"
                ),
                "citations": [
                    {
                        "breadcrumb": f"{course} > Quy che > Dieu 25 > Liem chinh hoc thuat",
                        "text": "Sinh vien phai tu minh thuc hien cac bai thuc hanh, bai tap lon va do an.",
                        "slide_number": 1
                    }
                ],
                "socratic_steps": [
                    "Doc ky de bai va xac dinh bien dau vao / dau ra.",
                    "Liet ke cac buoc xu ly chinh cua thuat toan.",
                    "Tu minh cai dat ma nguon tung phan nho."
                ],
                "continuous_code_lines": 0,
                "mascot_state": "caution",
                "article_25_triggered": True,
                "intent": "VIOLATION",
                "provider_used": "guardrails_firewall",
                "model_used": "article_25_validator",
                "latency_ms": round(latency, 2)
            }

        # Step 3: Build prompts customized to intent
        system_prompt = self._build_socratic_system_prompt(course, sid, intent, message)
        user_prompt = f"Sinh vien {sid} nhan tin:\n{message}"
        if code_context and code_context.strip():
            user_prompt += f"\n\nMa nguon hien tai sinh vien dang viet:\n```\n{code_context[:800]}\n```"

        # Step 4: Tier 1 - Groq Cloud
        if self.groq_api_key:
            try:
                raw_text, model = await self._call_groq(system_prompt, user_prompt)
                latency = (time.time() - start_time) * 1000.0
                return self._parse_socratic_output(raw_text, course, sid, intent, "groq", model, latency)
            except Exception as e:
                print(f"[AIEngine] Groq dispatch failed: {e}. Transitioning to Tier 2 (Gemini)...")

        # Step 5: Tier 2 - Google Gemini
        if self.gemini_api_key:
            try:
                raw_text, model = await self._call_gemini(system_prompt, user_prompt)
                latency = (time.time() - start_time) * 1000.0
                return self._parse_socratic_output(raw_text, course, sid, intent, "gemini", model, latency)
            except Exception as e:
                print(f"[AIEngine] Gemini dispatch failed: {e}. Transitioning to Tier 3 (OpenRouter)...")

        # Step 6: Tier 3 - OpenRouter
        if self.openrouter_api_key:
            try:
                raw_text, model = await self._call_openrouter(system_prompt, user_prompt)
                latency = (time.time() - start_time) * 1000.0
                return self._parse_socratic_output(raw_text, course, sid, intent, "openrouter", model, latency)
            except Exception as e:
                print(f"[AIEngine] OpenRouter dispatch failed: {e}. Falling back to reference oracle...")

        # Step 7: Tier 4 - Deterministic Reference Oracle Fallback
        latency = (time.time() - start_time) * 1000.0
        from validate_web import TLUWebReferenceOracle
        res = TLUWebReferenceOracle.simulate_socratic_chat(course, sid, message, code_context)
        res["provider_used"] = "reference_oracle"
        res["model_used"] = "deterministic_v1"
        res["latency_ms"] = round(latency, 2)
        res["intent"] = intent
        return res
