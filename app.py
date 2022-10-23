from flask import Flask, render_template, redirect, Response, url_for, request
import mysql.connector
import cv2
from PIL import Image
import numpy as np
import os
from playsound import playsound
import face_recognition

###################### init flask app ######################
app = Flask(__name__)

###################### mysql connect ######################
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="we674_db"
)
cursor = conn.cursor()

###################### function zone ######################
def generate_dataset(pid):
    face_classifier = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")

    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        if faces == ():
            return None
        for top, right, bottom, left in faces:
            cropped_face = img[right:right + left, top:top + bottom]
            cv2.rectangle(img, (top, right), (top + bottom, right + left), (26, 174, 10), 2)
            cv2.putText(img, "Scanning..", (top + 4, right + left + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (26, 174, 10), 1, cv2.LINE_AA)
        return cropped_face

    cap = cv2.VideoCapture(0)

    ## get max id
    cursor.execute("SELECT IFNULL(MAX(img_id), 0) FROM img_dataset")
    row = cursor.fetchone()
    img_id = row[0]
    max_id = img_id + 100
    count_img = 0

    while True:
        _, img = cap.read()
        if img == ():
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        for top, right, bottom, left in faces:
            cropped_face = img[right:right + left, top:top + bottom]

            if cropped_face is not None:
                count_img += 1
                img_id += 1
                face = cv2.resize(face_cropped(img), (250, 250))
                face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                file_name_path = "dataset/" + pid + "." + str(img_id) + ".jpg"
                cv2.imwrite(file_name_path, face_gray)
                cv2.rectangle(img, (top, right), (top + bottom, right + left), (26, 174, 10), 2)
                cv2.rectangle(img, (top - 1, right + left), (top + 1 + bottom, right + left + 20), (26, 174, 10), cv2.FILLED)
                cv2.putText(img, "Scanning.. " + str(count_img) + "%", (top + 4, right + left + 14), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                ## insert to db
                cursor.execute("""INSERT INTO `img_dataset`(`img_id`, `img_person`) VALUES('{}', '{}')""".format(img_id, pid))
                conn.commit()
                frame = cv2.imencode('.jpeg', img)[1].tobytes()
                yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                if cv2.waitKey(1) == 13 or int(img_id) == int(max_id):
                    playsound(r'static\\sounds\\success-sound-effect.mp3', True)
                    cap.release()
                    cv2.destroyAllWindows()
                    break

def get_face_recognition():
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, _, clf):
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = classifier.detectMultiScale(gray_image, scaleFactor, minNeighbors)
        coords = []
        for top, right, bottom, left in features:
            cv2.rectangle(img, (top, right), (top + bottom, right + left), color, 2)

            cv2.rectangle(img, (top - 1, right + left), (top + 1 + bottom, right + left + 20), color, cv2.FILLED)
            id, pred = clf.predict(gray_image[right:right + left, top:top + bottom])
            confidence = int(100 * (1 - pred / 300))
            cursor.execute("SELECT p.p_name FROM img_dataset AS i LEFT JOIN person_data AS p ON i.img_person = p.p_id WHERE i.img_id = " + str(id))
            name = cursor.fetchone()
            if name is not None:
                name = ''.join(name)
            if confidence > 70:
                label = name + " (" + str(confidence) + "%)"
                cv2.putText(img, label, (top + 4, right + left + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
            else:
                cv2.putText(img, "UNKNOWN", (top + 4, right + left + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
            coords = [top, right, bottom, left]
        return coords

    def recognize(img, clf, faceCascade):
        draw_boundary(img, faceCascade, 1.1, 10, (26, 174, 10), "Face", clf)
        return img

    faceCascade = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("resources/classifier.xml")

    videoCapture = cv2.VideoCapture(0)
    while videoCapture.isOpened():
        _, frame = videoCapture.read()
        _img = recognize(frame, clf, faceCascade)
        stream = cv2.imencode('.jpeg', _img)[1].tobytes()
        yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream + b'\r\n'
        if cv2.waitKey(1) == 27:
            videoCapture.release()
            cv2.destroyAllWindows()
            break
    else:
        print("camera not streaming.")

###################### route zone ######################
@app.route('/')
def index():
    cursor.execute("SELECT p_id, p_name, p_created FROM person_data WHERE p_status = 1")
    data = cursor.fetchall()
    return render_template('index.html', data=data)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/add_person')
def add_person():
    cursor.execute("SELECT IFNULL(MAX(p_id) + 1, 1000001) FROM person_data")
    row = cursor.fetchone()
    nid = row[0]
    return render_template('add_person.html', new_person_id=int(nid))


@app.route('/add_person_submit', methods=['POST'])
def add_person_submit():
    pid = request.form.get('p_id')
    pname = request.form.get('p_name')
    cursor.execute("""INSERT INTO `person_data`(`p_id`, `p_name`) VALUES('{}', '{}')""".format(pid, pname))
    conn.commit()
    return redirect(url_for('create_dataset', pid=pid))


@app.route('/stream_dataset/<pid>')
def stream_dataset(pid):
    return Response(generate_dataset(pid), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/create_dataset/<pid>')
def create_dataset(pid):
    return render_template('create_dataset.html', pid=pid)


@app.route('/train_classifier/<pid>')
def train_classifier(pid):
    dataset_dir = "dataset"
    path = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir)]
    faces = []
    ids = []
    for image in path:
        img = Image.open(image).convert('L')
        imageNp = np.array(img, 'uint8')
        id = int(os.path.split(image)[1].split(".")[1])
        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("resources/classifier.xml")
    return redirect('/')


@app.route('/face_recognition_feed')
def face_recognition_feed():
    return Response(get_face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/face_recognition')
def face_recognition():
    return render_template('face_recognition.html')


###################### start local server ######################
if __name__ == '__main__':
    app.run(debug=True)