# RAG Chatbot - Knowledge Assistant (Project Presentation)

Tài liệu này cung cấp các kịch bản trình bày, giải thích kiến trúc hệ thống và danh sách demo các tính năng chính của dự án, nhằm chuẩn bị cho buổi thuyết trình.

---

## 1. Tổng quan về đề tài của nhóm

**Tên Đề tài**: RAG Chatbot – AI Knowledge Assistant (Nhóm 3)

**Mục tiêu cốt lõi**: Xây dựng một trợ lý tri thức AI đa năng dựa trên công nghệ Retrieval-Augmented Generation (RAG). Hệ thống có khả năng biến bất kỳ bộ sưu tập tài liệu PDF nào thành một cơ sở tri thức số có thể tìm kiếm được một cách thông minh, hỗ trợ cả truy vấn bằng văn bản và hình ảnh.

**Vấn đề giải quyết**:
- Vượt qua hạn chế của "Tìm kiếm từ khóa" (Keyword Search) truyền thống bằng cách sử dụng "Tìm kiếm ngữ nghĩa" (Semantic Search) và "Hybrid Search" (kết hợp keyword + vector).
- Giải quyết bài toán trích xuất hình ảnh, biểu đồ, bảng biểu trong PDF vốn thường bị các công cụ OCR bỏ qua, thông qua công nghệ nhận diện hình ảnh (Vision AI) và Perceptual Hashing (aHash).
- Giải quyết vấn đề "ảo giác" (Hallucination) của các mô hình LLM lớn. Bot chỉ trả lời dựa trên ngữ cảnh được cung cấp từ tài liệu, đồng thời đưa ra trích dẫn nguồn (tên tài liệu, số trang) rõ ràng.

---

## 2. Giải thích System Diagram (Kiến trúc Hệ thống)

Để trình bày một ảnh sơ đồ duy nhất cho toàn bộ quy trình, Diagram nên được chia làm **2 luồng (Flows)** chính và bao gồm các Node sau:

### Các Thành phần (Nodes) cần có trong bản vẽ Diagram:
1. **Frontend (Streamlit UI)**: Nơi tương tác với người dùng, bao gồm các tab *Chat*, *Admin*, và *Visualize*.
2. **PDF Ingestion Pipeline (Luồng nhập liệu)**: 
   - Text Extractor (PyMuPDF).
   - Visual Extractor & Captioning (Google Gemini).
   - Text Splitter (Heading-aware Chunking).
   - Image Hashing (aHash).
3. **Embedding Model**: Chuyển đổi văn bản thành Vector (ví dụ: OpenAI `text-embedding-3-small`).
4. **Vector Database**: Trung tâm lưu trữ (Vector + Metadata). Bao gồm 2 nhánh (Automatic Fallback):
   - **Pinecone**: Lưu trữ Cloud, hỗ trợ Hybrid Search (Dense + BM25 Sparse).
   - **ChromaDB**: Lưu trữ Local Offline, hỗ trợ Dense Search.
5. **Retrieval Engine**: Xử lý truy vấn, kết hợp Deduplication (lọc trùng lặp bằng Cosine similarity).
6. **LLM Generation**: Mô hình sinh ngôn ngữ (OpenAI / Gemini / OpenRouter) nhận Context từ Database và Query từ User để tạo câu trả lời.
7. **Evaluation Module**: Đánh giá Q&A tự động đa luồng (Concurrent workers).

### Luồng Hoạt Động (Relationships):
* **Luồng 1 - Ingestion Flow (Quản trị viên tải tài liệu)**:
  `PDFs` ➔ `Ingestion Pipeline (Extract Text + Extract Images)` ➔ `Chunking & Visual Captioning` ➔ `Embedding Model` ➔ `Vector Database (Pinecone / ChromaDB)`
* **Luồng 2 - Query Flow (Người dùng hỏi đáp)**:
  `User Query (Text/Image)` ➔ `Frontend (Streamlit)` ➔ `Embedding Model / Image Hashing` ➔ `Retrieval Engine (Deduplication)` ➔ Truy xuất ngữ cảnh từ `Vector Database` ➔ `LLM Generation` ➔ Trả kết quả + Trích dẫn + TTS Audio ➔ `User`.

---

## 3. Demo những Feature có trong Project (Kịch bản Demo)

> **Lưu ý**: Cần đưa ra bằng chứng (evidence) trong quá trình demo bằng cách mở trực tiếp source code, log terminal, hoặc các file CSV kết quả để xác thực.

### Feature 1: Chức năng Chat & Hỏi đáp văn bản (Text Q&A) - Main Scenario
**Kịch bản**: Lấy 10 câu hỏi ngẫu nhiên từ tập dữ liệu `docs/Training_data_GD4/input/question.csv` để nhập vào chat UI, sau đó đối chiếu kết quả thực tế trên chatbot với đáp án lưu trong file `evaluation_results.csv`.

| STT | Câu hỏi Demo | Đáp án kỳ vọng (Dựa trên CSV) |
|-----|--------------|------------------------------|
| 1 | Cơ chế lưu trữ năng lượng của siêu tụ điện dựa trên gì? | **B** (Tích tụ ion ở bề mặt điện cực tạo điện trường) |
| 2 | Một pixel của ảnh xám có thể nhận giá trị tối thiểu và tối đa lần lượt là? | **C** (0 và 255) |
| 3 | Nếu trong quá trình khoan, cao độ dung dịch khoan phải luôn cao hơn mực nước ngầm ít nhất 1,5 m... | **B** (-8,5 m) |
| 4 | Trong giải thuật DES, kích thước hiệu dụng của khóa là bao nhiêu bit? | **B** (56 bit) |
| 5 | Cảm biến nào giúp robot điều chỉnh lực cầm nắm chính xác? | **D** (Cảm biến xúc giác và lực) |
| 6 | Theo tài liệu, để thêm nhãn dữ liệu trong Tableau, bước đầu tiên cần thực hiện là gì? | **B** (Click chọn Data Labels > New Label) |
| 7 | Mục đích chính của việc xây dựng Cổng kết nối dịch vụ chứng thực chữ ký số công cộng là gì? | **B** (Để kết nối dịch vụ chứng thực chữ ký số công cộng với các HTTT...) |
| 8 | Thông tư Public_257 quy định những yêu cầu kỹ thuật nào đối với phần mềm ký số...? | **A** |
| 9 | Theo tài liệu Public_163, phiên bản TLS nào được sử dụng rộng rãi nhất? | **C** |
| 10 | Thách thức lớn nhất để triển khai đại trà giao thông hydro? | **A** |

**Bằng chứng (Evidence)**: 
1. Sau khi Bot trả lời, chỉ ra **Citation (Trích dẫn)** bên dưới câu trả lời (Tên file, Số trang). 
2. Mở file `evaluation_results.csv` tại dòng tương ứng của câu hỏi để xác nhận model đánh giá cũng đưa ra đúng lựa chọn đó (Ví dụ cột `correct_answer` = B và cột `ai_answer_...` = B).

### Feature 2: Image-based Retrieval (Tìm kiếm & Chat bằng Hình ảnh)
- **Kịch bản**: Upload hoặc paste một tấm ảnh biểu đồ/bảng biểu đã được cắt từ PDF (có thể lấy từ `test_crop.png` hoặc `test_crop2.png` trong repo) vào ô chat. Hỏi: *"Bức ảnh này nói về điều gì?"* hoặc *"Thông tin trong bảng này nằm ở tài liệu nào?"*
- **Bằng chứng**: Bot sẽ áp dụng thuật toán `aHash` (Perceptual Hashing) để tìm đúng bức ảnh trong cơ sở dữ liệu. Chỉ ra phần log terminal hoặc metadata trong UI chat để thấy hình ảnh match dựa vào chỉ số `Hamming distance`, và đọc `Visual Caption` mà Gemini đã mô tả để sinh câu trả lời.

### Feature 3: Automatic Database Fallback & Hybrid Search
- **Kịch bản**: 
  1. Chứng minh **Hybrid Search**: Mở file `.env`, cho thấy `PINECONE_API_KEY` đang hoạt động. Tìm kiếm một câu hỏi đòi hỏi đối sánh từ khóa chính xác (BM25 sparse) + ngữ nghĩa.
  2. Chứng minh **Fallback**: Vào `.env` ẩn/xóa `PINECONE_API_KEY` đi, reload app. Hệ thống sẽ **tự động chuyển sang sử dụng ChromaDB cục bộ** (Local Dense Vector Store) mà không bị crash.
- **Bằng chứng**: Chuyển sang Tab `Admin` trên UI Streamlit, chỉ vào mục "Active Vector Database" đang tự động hiển thị chuyển từ Pinecone sang ChromaDB.

### Feature 4: Admin Evaluation System (Đánh giá hàng loạt)
- **Kịch bản**: Vào tab **Admin ➔ Evaluation**. Chọn cấu hình chạy batch khoảng 5-10 câu hỏi với *Concurrency (số luồng)* = 5. Bấm chạy.
- **Bằng chứng**: Mở thư mục code, hiển thị file `evaluation_results_metadata.json` và `evaluation_results.csv` vừa được cập nhật timestamp mới nhất, trong đó ghi rõ độ chính xác (Accuracy), cấu hình model đã dùng, số worker và thời gian chạy. 

### Feature 5: Visualization & Usage Tracking
- **Kịch bản (Visualize)**: Mở tab **Visualize**. Hiển thị biểu đồ 3D PCA Galaxy hoặc 2D t-SNE scatter. Chứng minh các trang PDF cùng chủ đề nằm gần nhau trong không gian vector không gian 3 chiều.
- **Kịch bản (Usage Tracking)**: Vào tab **Admin ➔ Usage & Cost**.
- **Bằng chứng**: Mở file `usage_log.json` và `budget_config.json` để cho thấy hệ thống đang liên tục track số token tiêu thụ, quy đổi ra chi phí USD, và có thể cảnh báo nếu vượt mức giới hạn (ví dụ vượt 9$). 

### Feature 6: Trích xuất hình ảnh thông minh (Visual Extraction Pipeline)
- **Kịch bản**: Giải thích cách hệ thống nhận diện ảnh trong PDF lúc ingest.
- **Bằng chứng**: Mở file code `src/ingest/image_extraction.py` và `src/ingest/visual_caption.py` để chứng minh hệ thống không chỉ bóc tách chữ, mà còn cắt hình ảnh ra, gửi cho Vision AI (Gemini) để sinh Caption (mô tả ngữ nghĩa), và lưu lại toạ độ (spatial IDs) để đảm bảo không bị lẫn lộn giữa các ảnh.
