# Detect-face
**Hệ thống Nhận diện Khuôn mặt & Điều khiển Thiết bị (IoT)**
Dự án này là hệ thống nhận diện khuôn mặt thời gian thực sử dụng Streamlit và OpenCV, kết hợp với Wemos D1 R2 (ESP8266) để điều khiển thiết bị ngoại vi (Đèn/Servo) dựa trên danh tính người được nhận diện.

**🚀 Tính năng**
Nhận diện khuôn mặt: Nhận diện người dùng từ Webcam và so sánh với dữ liệu đã lưu.

Quản lý người dùng: Thêm, xóa hoặc đổi tên người dùng trực tiếp trên giao diện web.

Điều khiển IoT: Gửi lệnh qua HTTP để điều khiển Đèn (Relay) hoặc Servo gắn trên Wemos D1 R2.

Hiển thị trực tiếp: Theo dõi luồng video và FPS ngay trên trình duyệt.

**🛠 Công nghệ sử dụng**
Python: Streamlit, OpenCV, Face_recognition.

Phần cứng: Wemos D1 R2 (ESP8266), Servo SG90 hoặc Module Relay.

Giao thức: HTTP (Gửi lệnh từ Python lên ESP8266).

**⚙️ Hướng dẫn cài đặt**
1. Phía Hardware (Wemos D1 R2)
Kết nối Wemos với mạng Wi-Fi của bạn.

Nạp code Arduino (có trong thư mục /firmware) lên Wemos.

Đảm bảo chân D1 (cho Servo) hoặc D5 (cho Relay) được kết nối đúng.

Ghi lại địa chỉ IP của Wemos (ví dụ: 192.168.1.15).

2. Phía Software (Python)
Cài đặt các thư viện cần thiết:

Bash
pip install streamlit opencv-python face_recognition requests


Mở file app.py và cập nhật địa chỉ IP của Wemos:

Python
WEMOS_IP = "http://192.168.1.15" 
Chạy ứng dụng:

Bash
streamlit run app.py
