from enum import Enum


class CustomAssistantResponse(str, Enum):
    RESPONSE_ON_COMPLETION_FAILURE = "Sorry, I have been raised a problem on generating a consultancy on you :("
    RESPONSE_ON_DOMAIN_MISMATCH = "Sorry, your question is mismatched with my domain of expertisement. Try again with another input."
