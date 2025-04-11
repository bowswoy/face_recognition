from flask import Flask, render_template, redirect, Response, url_for, request
import mysql.connector
import cv2
from PIL import Image
import numpy as np
import os
from playsound import playsound
import mediapipe as mp
import time

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

###################### global variable ######################
count = 0
pause_count = 0
scanned = False

###################### function zone ######################


def generate_dataset(pid):
    face_classifier = cv2.CascadeClassifier(
        "resources/haarcascade_frontalface_default.xml")

    cap = cv2.VideoCapture(0)

    # get max id
    cursor.execute("SELECT IFNULL(MAX(img_id), 0) FROM img_dataset")
    row = cursor.fetchone()
    img_id = row[0]
    max_id = img_id + 100
    count_img = 0

    delay = 0
    time.sleep(1.5)
    playsound('static/sounds/before-scan.mp3', False)
    cropped_face = None
    while True:
        _, img = cap.read()
        if img is None:
            return None

        delay += 1
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        for top, right, bottom, left in faces:
            cropped_face = img[right:right + left, top:top + bottom]

            if cropped_face is not None:

                cv2.rectangle(img, (top, right), (top + bottom, right + left), (26, 174, 10), 2)
                cv2.rectangle(img, (top - 1, right + left), (top + 1 + bottom, right + left + 40), (26, 174, 10), cv2.FILLED)

                if delay >= 50:
                    count_img += 1
                    img_id += 1
                    face = cv2.resize(cropped_face, (250, 250))
                    face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                    file_name_path = "dataset/" + pid + "." + str(img_id) + ".jpg"
                    cv2.imwrite(file_name_path, face_gray)
                    if count_img < 100:
                        cv2.putText(img, "Scanning.. " + str(count_img) + "%", (top + 4, right + left + 28), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.putText(img, "Complete", (top + 4, right + left + 28), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                    # insert to db
                    cursor.execute("""INSERT INTO `img_dataset`(`img_id`, `img_person`) VALUES('{}', '{}')""".format(img_id, pid))
                    conn.commit()
                    frame = cv2.imencode('.jpeg', img)[1].tobytes()
                    yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                    if cv2.waitKey(1) == 13 or int(img_id) == int(max_id):
                        delay = 0
                        cap.release()
                        cv2.destroyAllWindows()
                        playsound('static/sounds/success-sound-effect.mp3', False)
                        playsound('static/sounds/scan-success.mp3', False)
                        # playsound('static/sounds/complete.mp3', False)
                        break
                else:
                    cv2.putText(img, "Preparing.. ", (top + 4, right + left + 28), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                    frame = cv2.imencode('.jpeg', img)[1].tobytes()
                    yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                    if cv2.waitKey(1) == 13:
                        cap.release()
                        cv2.destroyAllWindows()
                        break


def get_face_recognition():
    faceCascade = cv2.CascadeClassifier(
        "resources/haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("resources/classifier.xml")

    videoCapture = cv2.VideoCapture(0)
    while videoCapture.isOpened():
        _, image = videoCapture.read()
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        features = faceCascade.detectMultiScale(gray_image, 1.3, 5)
        for top, right, bottom, left in features:
            cv2.rectangle(image, (top, right), (top + bottom,
                          right + left), (26, 174, 10), 2)
            cv2.rectangle(image, (top - 1, right + left), (top + 1 +
                          bottom, right + left + 40), (26, 174, 10), cv2.FILLED)
            id, pred = clf.predict(
                gray_image[right:right + left, top:top + bottom])
            confidence = int(100 * (1 - pred / 300))
            cursor.execute(
                "SELECT p.p_name FROM img_dataset AS i LEFT JOIN person_data AS p ON i.img_person = p.p_id WHERE i.img_id = " + str(id))
            row = cursor.fetchone()
            uname = row[0]
            if confidence > 70:
                label = uname + " (" + str(confidence) + "%)"
                cv2.putText(image, label, (top + 4, right + left + 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(image, "Unknown", (top + 4, right + left + 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        stream = cv2.imencode('.jpeg', image)[1].tobytes()
        yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream + b'\r\n'
        if cv2.waitKey(1) == 27:
            videoCapture.release()
            cv2.destroyAllWindows()
            break
    else:
        print("camera not streaming.")


def get_face_check_in():
    faceCascade = cv2.CascadeClassifier(
        "resources/haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("resources/classifier.xml")

    videoCapture = cv2.VideoCapture(0)

    mpHands = mp.solutions.hands
    hands = mpHands.Hands()
    mpDrawing = mp.solutions.drawing_utils
    mpDrawingStyles = mp.solutions.drawing_styles

    i = 0
    c = 0
    while videoCapture.isOpened():
        _, image = videoCapture.read()
        imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(imageRGB)

        fingerCount = 0

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:  # working with each hand

                handIndex = results.multi_hand_landmarks.index(handLms)
                handLabel = results.multi_handedness[handIndex].classification[0].label
                # print(handLabel)

                handLandmarks = []
                for landmarks in handLms.landmark:
                    handLandmarks.append([landmarks.x, landmarks.y])

                if handLabel == "Left" and handLandmarks[4][0] > handLandmarks[3][0]:
                    fingerCount = fingerCount+1
                elif handLabel == "Right" and handLandmarks[4][0] < handLandmarks[3][0]:
                    fingerCount = fingerCount+1

                if handLandmarks[8][1] < handLandmarks[6][1]:  # นิ้วชี้
                    fingerCount = fingerCount+1
                if handLandmarks[12][1] < handLandmarks[10][1]:  # นิ้วกลาง
                    fingerCount = fingerCount+1
                if handLandmarks[16][1] < handLandmarks[14][1]:  # นิ้วนาง
                    fingerCount = fingerCount+1
                if handLandmarks[20][1] < handLandmarks[18][1]:  # นิ้วก้อย
                    fingerCount = fingerCount+1

                mpDrawing.draw_landmarks(
                    image,
                    handLms,
                    mpHands.HAND_CONNECTIONS,
                    mpDrawingStyles.get_default_hand_landmarks_style(),
                    mpDrawingStyles.get_default_hand_connections_style()
                )
            c += 1
            # cv2.putText(
            #     image,
            #     str(c), (500, 100),
            #     cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 10
            # )
        else:
            c = 0

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        features = faceCascade.detectMultiScale(gray_image, 1.3, 5)
        for top, right, bottom, left in features:
            cv2.rectangle(image, (top, right), (top + bottom,
                          right + left), (26, 174, 10), 2)
            cv2.rectangle(image, (top - 1, right + left), (top + 1 +
                          bottom, right + left + 40), (26, 174, 10), cv2.FILLED)
            id, pred = clf.predict(
                gray_image[right:right + left, top:top + bottom])
            confidence = int(100 * (1 - pred / 300))
            cursor.execute(
                "SELECT p.p_id, p.p_name FROM img_dataset AS i LEFT JOIN person_data AS p ON i.img_person = p.p_id WHERE i.img_id = " + str(id))
            row = cursor.fetchone()
            uid = row[0]
            uname = row[1]
            if confidence > 70:
                label = uname + " (" + str(confidence) + "%)"
                cv2.putText(image, label, (top + 4, right + left + 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                if fingerCount == 5 and c <= 30:
                    status = 'Checking in...'
                    i += 1
                    loading = (i / 15) * bottom
                    cv2.rectangle(image, (top, right + left + 40), (top + 1 +
                                  int(loading), right + left + 50), (0, 255, 255), cv2.FILLED)
                    if i == 15:
                        i = 0
                        c = 31
                        cursor.execute("INSERT INTO check_in(p_id) VALUES({})".format(uid))
                        conn.commit()
                        status = 'Success'
                        playsound('static/sounds/success-sound-effect.mp3', False)
                        playsound('static/sounds/success.mp3', False)

                    cv2.putText(image, status, (top, right - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                else:
                    i = 0
            else:
                cv2.putText(image, "Unknown", (top + 4, right + left + 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        stream = cv2.imencode('.jpeg', image)[1].tobytes()
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
    cursor.execute(
        "SELECT p_id, p_name, p_created FROM person_data WHERE p_status = 1")
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
    cursor.execute(
        """INSERT INTO `person_data`(`p_id`, `p_name`) VALUES('{}', '{}')""".format(pid, pname))
    conn.commit()
    return redirect(url_for('create_dataset', pid=pid))


@app.route('/stream_dataset/<pid>')
def stream_dataset(pid):
    return Response(generate_dataset(pid), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/create_dataset/<pid>')
def create_dataset(pid):
    return render_template('create_dataset.html', pid=pid)


@app.route('/train_classifier')
def train_classifier():
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


@app.route('/check_in_feed')
def check_in_feed():
    return Response(get_face_check_in(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/check_in')
def check_in():
    return render_template('check_in.html')


@app.route('/list_check_in')
def list_check_in():
    cursor.execute(
        "SELECT p.p_name, MIN(c.c_datetime) AS f_time, MAX(c.c_datetime) AS l_time FROM check_in AS c LEFT JOIN person_data AS p ON(c.p_id = p.p_id) WHERE DATE(c.c_datetime) = CURDATE() GROUP BY c.p_id ORDER BY c.c_datetime ASC")
    data = cursor.fetchall()
    return render_template('list_check_in.html', data=data)


###################### start local server ######################
if __name__ == '__main__':
    app.run(host='127.0.0.1',debug=True)
