import sys, os
sys.path.append(os.getcwd())
from src.rag.service import RAGService
service = RAGService()

# Simulate the exact query generated from the screenshot
query = "Biểu đồ hiển thị một hệ trục tọa độ Descartes 2D với một đường cong parabol và các điểm minh họa thuật toán gradient descent. Trục hoành (x-axis) có các giá trị -2, 0, 2, trong khi trục tung (y-axis) có các giá trị 0, 2, 4. Đường cong màu nâu đỏ có dạng parabol mở lên trên, với đỉnh tại gốc tọa độ (0,0), có vẻ là đồ thị của hàm số y = x^2. Các điểm: Điểm A (màu xanh dương) tại khoảng (-2.1, 4.4). Điểm B... Các mũi tên màu đen chỉ hướng di chuyển."

with open('sim_query.txt', 'w', encoding='utf-8') as f:
    results = service.retrieve(query)
    for idx, r in enumerate(results):
        f.write(f"{idx+1}. Page {r.page} | Score {r.score:.4f} | ContentType: {r.content_type} | Text: {r.text[:100].replace(chr(10), ' ')}\n")
