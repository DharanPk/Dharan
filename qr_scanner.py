import cv2
from pyzbar.pyzbar import decode

def scan_qr_code():
    cap = cv2.VideoCapture(0)  # 0 is for the default camera

    while True:
        _, frame = cap.read()  # Capture frame
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            qr_code_data = obj.data.decode('utf-8')
            print("QR Code Data:", qr_code_data)
            cap.release()  # Release the camera once a QR code is found
            return qr_code_data

        cv2.imshow("QR Code Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    scan_qr_code()
