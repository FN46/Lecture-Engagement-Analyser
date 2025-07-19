import cv2
from deepface import DeepFace
from PIL import Image, ImageTk

class FaceAnalysis:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError("Error opening webcam")
        
        
    def analyse_single_frame(self, frame):
        """
        Perform face analysis on a single frame.
        Returns list of face analysis results.
        """
        return self.process_frame_for_analysis(frame)


    def calculate_engagement(self, emotion):
        engagement_levels = {
            "happy": 0.9,
            "surprise": 0.85,
            "neutral": 0.7,
            "sad": 0.3,
            "angry": 0.2,
            "fear": 0.4,
            "disgust": 0.2
        }

        nervous_emotions = ["fear", "angry", "disgust"]
        excited_emotions = ["surprise", "happy"]

        emotion_lower = emotion.lower()
        engagement = engagement_levels.get(emotion_lower, 0.5)
        state = "nervous" if emotion_lower in nervous_emotions else "excited" if emotion_lower in excited_emotions else emotion_lower

        return round(engagement * 100, 1), state

    def analyze_feed(self):
        print("Starting webcam. Press 'q' to quit.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            try:
                results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

                for result in results:
                    region = result['region']
                    dominant_emotion = result['dominant_emotion']
                    engagement_score, emotional_state = self.calculate_engagement(dominant_emotion)

                    x, y, w, h = region['x'], region['y'], region['w'], region['h']
                    if x >= 0 and y >= 0:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

                        text = f"{dominant_emotion} ({emotional_state}), {engagement_score}%"
                        cv2.putText(frame, text, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            except Exception as e:
                print("Emotion detection error:", str(e))

            cv2.imshow('Engagement Detector', frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        self.cleanup()
        
    def get_frame_analysis(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        try:
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

            output = []
            for result in results:
                region = result['region']
                emotion = result['dominant_emotion']
                engagement_score, state = self.calculate_engagement(emotion)

                output.append({
                    "emotion": emotion,
                    "engagement": engagement_score,
                    "state": state,
                    "region": region,
                })
            return output

        except Exception as e:
            print("Face analysis error:", e)
            return None
    
    def get_annotated_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        try:
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            for result in results:
                region = result.get("region", {})
                x = region.get("x", 0)
                y = region.get("y", 0)
                w = region.get("w", 0)
                h = region.get("h", 0)
                emotion = result["dominant_emotion"]
                engagement_score, state = self.calculate_engagement(emotion)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                label = f"{emotion} ({state}) - {engagement_score}%"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        except Exception as e:
            print("Face analysis error:", e)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        return ImageTk.PhotoImage(image=img)


    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    fa = FaceAnalysis()
    fa.analyze_feed()
