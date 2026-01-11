import cv2
import mediapipe as mp
import time

class ArmDetector:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.last_state = "DOWN"
        self.last_trigger_time = 0
        self.cooldown = 0.4  # seconds


        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.last_finger_time = 0
        self.finger_cooldown = 1.0  # seconds


    def get_arm_up_event(self):
        
        ret, frame = self.cap.read()
        if not ret:
            return False
        self.frame = frame

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)

        current_state = "DOWN"

        if result.pose_landmarks:
            lm = result.pose_landmarks.landmark

            shoulder = lm[11]   # LEFT_arm
            wrist = lm[15]      # LEFT wrist

            # ARM LOGIC 
            if wrist.y < shoulder.y:
                current_state = "UP"

            # Marking
            self.mp_draw.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )

            h, w, _ = frame.shape
            sx, sy = int(shoulder.x * w), int(shoulder.y * h)
            wx, wy = int(wrist.x * w), int(wrist.y * h)

            cv2.circle(frame, (sx, sy), 10, (0, 0, 255), -1)   # shoulder (RED)
            cv2.circle(frame, (wx, wy), 10, (255, 0, 0), -1)  # wrist (BLUE)

        # EVENT (DOWN UP) 
        now = time.time()
        event = False

        if (
            current_state == "UP"
            and self.last_state == "DOWN"
            and now - self.last_trigger_time > self.cooldown
        ):
            event = True
            self.last_trigger_time = now

        self.last_state = current_state

        #  STATUS TEXT 
        status_text = "ARM UP" if current_state == "UP" else "ARM DOWN"
        cv2.putText(
            frame,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        #  SIDE WINDOW 
        cv2.imshow("Camera", frame)
        cv2.waitKey(1)

        return  event
    




    def get_finger_count(self):
        
        if not hasattr(self, "frame"):
            return None

        frame = self.frame


        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return None

        hand = result.multi_hand_landmarks[0]
        lm = hand.landmark

        # Count 
        fingers_up = [
            lm[8].y < lm[6].y,    # index
            lm[12].y < lm[10].y,  # middle
            lm[16].y < lm[14].y   # ring
        ]

        count = fingers_up.count(True)
        now = time.time()

        cv2.putText(
        frame,
        f"FINGERS: {count}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2
        )


        # Cooldown 
        if now - self.last_finger_time > self.finger_cooldown:
            self.last_finger_time = now
            return count

        return None

    

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

