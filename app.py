import os
import cv2
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_file():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_and_cartoonize():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file'
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        if filename.lower().endswith(('jpg', 'jpeg', 'png')):
            cartoonized_image = cartoonize_image(file_path)
            cartoonized_filename = f'cartoon_{filename}'
            cartoonized_image_path = os.path.join(app.config['UPLOAD_FOLDER'], cartoonized_filename)
            cv2.imwrite(cartoonized_image_path, cartoonized_image)
            return render_template('processed.html', filename=cartoonized_filename)
        
        elif filename.lower().endswith('mp4'):
            cartoonized_video_filename = f'cartoon_{filename}'
            cartoonized_video_path = os.path.join(app.config['UPLOAD_FOLDER'], cartoonized_video_filename)
            cartoonize_video(file_path, cartoonized_video_path)
            return render_template('processed.html', filename=cartoonized_video_filename)

    return 'File type not allowed'

def cartoonize_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 7, 100, 100)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

def cartoonize_video(video_in_path, video_out_path):
    cap = cv2.VideoCapture(video_in_path)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    
    writer = cv2.VideoWriter(video_out_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))  # Use 'mp4v' for compatibility
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(frame, 7, 100, 100)
        cartoon_frame = cv2.bitwise_and(color, color, mask=edges)
        writer.write(cartoon_frame)

    cap.release()
    writer.release()

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
