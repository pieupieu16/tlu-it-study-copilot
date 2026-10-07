# TLU IT Study Copilot - Trợ Lý Học Tập Thông Minh Cho Sinh Viên CNTT Đại Học Thăng Long

Nền tảng trợ lý học tập trực tuyến dành riêng cho sinh viên Khoa Công nghệ Thông tin - Trường Đại học Thăng Long (TLU). Hệ thống tích hợp mô hình suy luận đa tầng (Groq Cloud, Google Gemini, OpenRouter), giao diện Khung Chiếu Slide 16:9 cinematic (lấy cảm hứng từ K3-Hackathon), Chatbot linh vật Rồng TLU nổi kiểu Messenger và Studio thực hành lập trình theo phương pháp Socratic tuân thủ Điều 25 Quy chế Liêm chính Học thuật.

---

## Tính Năng Nổi Bật

1. **Khung Chiếu Slide 16:9 & Bảng Điều Khiển Lớp Học (Classroom Stage)**:
   - Sân khấu trình chiếu 16:9 với phong cách thẻ dập khối Block-Card (`border-2 border-b-4`).
   - Thanh tiến trình đọc slide tự động và bộ đếm trang chuẩn tabular.
   - Cụm điều khiển phóng to / thu nhỏ slide (`[-]`, `100%`, `[+]`, `Ctrl + Wheel`).
   - Chế độ Theo dõi giảng viên vs. Tự đọc độc lập kèm banner cảnh báo đồng bộ.
   - Bảng trợ giảng Socratic Split-View AI Study Panel đặt song song với slide.

2. **Chatbot Linh Vật Rồng TLU Nổi (Floating Messenger Mascot)**:
   - Bong bóng Messenger nổi góc màn hình kèm hiệu ứng cảm xúc (hân hoan, cảnh báo Điều 25, bối rối, vẫy tay).
   - Định hướng giải thích mã nguồn Socratic cho 5 môn học cốt lõi: IT101 (C/C++), IT201 (Java), IT205 (SQL), IT301 (Python Socket), IT315 (Kiến trúc máy tính & HĐH).

3. **Cổng Đăng Nhập & Phân Quyền Sinh Viên / Quản Trị**:
   - Màn hình đăng nhập hiển thị linh vật Rồng TLU cỡ lớn vẫy tay chào đón sinh viên.
   - Hỗ trợ tài khoản sinh viên Nguyễn Văn An (A41234), Trần Mai Linh (A38901) và Cổng Quản trị Vận hành `/admin`.

4. **Kiến Trúc AI Đa Tầng (Multi-Provider AI Engine)**:
   - Tự động định tuyến thông minh: Groq Cloud (Qwen 3.8 27B / GPT-OSS 120B siêu tốc độ) -> Google Gemini 3.5 Flash Lite -> OpenRouter -> Reference Oracle.

5. **Quy Chuẩn Thiết Kế & An Toàn**:
   - 100% Light Mode (nền sáng tiêu chuẩn giảng đường).
   - Zero Icons (sử dụng 100% typography, thẻ badge và CSS shape).
   - Rào chắn an toàn 4 lớp Guardrails, khử PII tiếng Việt bảo lưu Mã SV, chống giải hộ mã nguồn vi phạm Điều 25 TLU.

---

## Cài Đặt & Khởi Chạy

### 1. Yêu Cầu Môi Trường
- Python 3.10 trở lên
- Trình duyệt web hiện đại (Google Chrome, Microsoft Edge, Firefox)

### 2. Cài Đặt Thư Viện
```bash
pip install fastapi uvicorn pydantic requests
```

### 3. Cấu Hình Biến Môi Trường
Sao chép tệp mẫu và điền API keys của bạn:
```bash
cp .env.example .env
```

### 4. Khởi Động Server
```bash
python3 app.py
```
Truy cập vào ứng dụng tại: `http://localhost:8000`

---

## Kiểm Thử & Nghiệm Thu

Hệ thống đi kèm bộ kiểm thử tự động toàn diện:
```bash
# Kiểm thử thẩm định nghiêm ngặt toàn hệ thống (315 tiêu chí)
python3 validate_web.py --strict

# Kiểm thử tự động toàn bộ 35 nút bấm trên trình duyệt Google Chrome thật
python3 test_all_buttons.py

# Kiểm thử các tính năng lớp học K3-Hackathon
python3 test_k3_slide_viewer.py
```
