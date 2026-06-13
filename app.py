import streamlit as st
import cv2
import face_recognition
import numpy as np
import os
import pickle
import time
import requests

WEMOS_IP = "http://192.168.5.103"
# Cấu hình thư mục lưu trữ
FACES_DIR = "faces"
DATA_FILE = "face_data.pkl"
if not os.path.exists(FACES_DIR): os.makedirs(FACES_DIR)

admin_names = ["Admin", "Minh Tin"]  # Danh sách tên người được phép mở cửa (có thể thêm nhiều tên)

st.set_page_config(layout="wide")
st.title("Hệ thống Nhận diện Khuôn mặt AI")

# --- XỬ LÝ DỮ LIỆU ---
def load_known_faces():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "rb") as f:
                # Kiểm tra xem file có nội dung không
                if os.path.getsize(DATA_FILE) > 0:
                    return pickle.load(f)
                else:
                    return [], []
        except (pickle.UnpicklingError, EOFError):
            print("File dữ liệu bị hỏng, đang tạo mới...")
            return [], []
    return [], []

def save_known_faces(encs, names):
    with open(DATA_FILE, "wb") as f:
        pickle.dump((encs, names), f)

def count_cameras():
    count = 0
    while True:
        cap = cv2.VideoCapture(count)
        if not cap.isOpened():
            break
        print(f"Tìm thấy Camera ID: {count}")
        cap.release()
        count += 1
    return count

print(f"Tổng cộng có {count_cameras()} camera được kết nối.")

known_encodings, known_names = load_known_faces()

# --- GIAO DIỆN ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Quản lý người dùng")
    name_input = st.text_input("Nhập tên người mới:")
    
    if st.button("Lưu khuôn mặt"):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb)
            if encs:
                known_encodings.append(encs[0])
                known_names.append(name_input)
                save_known_faces(known_encodings, known_names)
                cv2.imwrite(f"{FACES_DIR}/{name_input}.jpg", frame)
                st.success(f"Đã lưu: {name_input}")
                st.rerun() # Tự làm mới trang để cập nhật danh sách
            else:
                st.error("Không tìm thấy khuôn mặt!")
        cap.release()
    
    st.divider()
    st.subheader("Danh sách đã lưu:")
    
    for i, name in enumerate(known_names):
        with st.expander(f"👤 {name}"):
            new_name = st.text_input(f"Đổi tên cho {name}:", key=f"input_{name}")
            col_a, col_b = st.columns(2)
            
            if col_a.button("Đổi tên", key=f"rename_{name}"):
                if new_name and new_name != name:
                    # 1. Cập nhật tên trong list
                    known_names[i] = new_name
                    save_known_faces(known_encodings, known_names)
                    
                    # 2. Đổi tên file ảnh trên ổ cứng
                    old_path = os.path.join(FACES_DIR, f"{name}.jpg")
                    new_path = os.path.join(FACES_DIR, f"{new_name}.jpg")
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                    
                    st.rerun()
            
            if col_b.button("Xóa", key=f"delete_{name}"):
                known_encodings.pop(i)
                known_names.pop(i)
                save_known_faces(known_encodings, known_names)
                if os.path.exists(os.path.join(FACES_DIR, f"{name}.jpg")):
                    os.remove(os.path.join(FACES_DIR, f"{name}.jpg"))
                st.rerun()

    st.divider()
    
    # Lựa chọn ID Camera
    cam_id = st.number_input("Chọn Camera ID (thường là 0):", min_value=0, max_value=5, value=0)
    
    # Lựa chọn độ phân giải
    res_option = st.selectbox("Chọn độ phân giải:", ["640x480", "1280x720", "1920x1080"])
    
    # Lưu lựa chọn vào session state
    if st.button("Áp dụng cấu hình"):
        st.session_state.cam_id = cam_id
        st.session_state.res = res_option
        st.rerun()

with col2:
    st.header("Camera trực tiếp")
    frame_window = st.image([])
    camera = cv2.VideoCapture(0)
    
    # THIẾT LẬP ĐỘ PHÂN GIẢI
    # Thiết lập mặc định nếu chưa chọn
    if 'cam_id' not in st.session_state: st.session_state.cam_id = 0
    if 'res' not in st.session_state: st.session_state.res = "640x480"
    
    # Sử dụng giá trị từ session state để khởi tạo camera
    width, height = map(int, st.session_state.res.split('x'))
    camera = cv2.VideoCapture(st.session_state.cam_id)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Biến quản lý FPS
    frame_count = 0
    face_locations = []
    face_names = []
    prev_time = 0
    fps = 0
    fps_list = []
    scale_factor = 0.25 # Giảm kích thước để tăng tốc độ xử lý

    while True:
        ret, frame = camera.read()
        if not ret: break
        
        # Chỉ xử lý nhận diện mỗi 5 frame một lần để đạt FPS cao
        if frame_count % 5 == 0:
            small_frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            encs = face_recognition.face_encodings(rgb_small_frame, face_locations)
            if not encs: requests.get(f"{WEMOS_IP}/off")
            face_names = []
            for enc in encs:
                name = "Unknown"
                if known_encodings:
                    dists = face_recognition.face_distance(known_encodings, enc)
                    best = np.argmin(dists)
                    if dists[best] < 0.5: 
                        name = known_names[best]
                face_names.append(name)
            for name in face_names:
                # Gửi lệnh nếu là người được phép (ví dụ: tên là "Admin")
                if name in admin_names:
                    requests.get(f"{WEMOS_IP}/on")
                    print("on")
                else:
                    requests.get(f"{WEMOS_IP}/off")
                    print("off")
            
        
        frame_count += 1
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time
        fps_list.append(fps)
        if len(fps_list) > 10: fps_list.pop(0) # Giữ 10 giá trị gần nhất
        avg_fps = sum(fps_list) / len(fps_list)
        
        # Vẽ khung (nhân 4 vì đã resize 0.25)
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(frame, f"FPS: {int(avg_fps)}", (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        frame_window.image(frame, channels="BGR")