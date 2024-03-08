from enum import Enum


class Emotion(str, Enum):
    ANGER = "anger",
    CONTEMPT = "contempt",
    DISGUST = "disgust",
    FEAR = "fear",
    HAPPY = "happy",
    NEUTRAL = "neutral",
    SAD = "sad"
    SURPRISE = "surprise"
