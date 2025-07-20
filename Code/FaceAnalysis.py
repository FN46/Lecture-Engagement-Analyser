import cv2
from deepface import DeepFace

class FaceAnalysis:
    def __init__(self):
        self.detector_backend = 'opencv' 

    def analyse_single_frame(self, frame):
        """
        Perform face analysis using DeepFace.
        Returns list of dictionaries with emotion, state, and engagement.
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = DeepFace.analyze(
                img_path=rgb_frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend=self.detector_backend
            )

            output = []
            for result in results:
                emotion = result.get("dominant_emotion", "neutral")
                engagement, state = self.calculate_engagement(emotion)

                output.append({
                    "emotion": emotion,
                    "engagement": engagement,
                    "state": state
                })

            return output

        except Exception as e:
            print("Face analysis error:", e)
            return []

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
        state = (
            "nervous" if emotion_lower in nervous_emotions
            else "excited" if emotion_lower in excited_emotions
            else emotion_lower
        )

        return round(engagement * 100, 1), state
