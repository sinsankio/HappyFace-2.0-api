import base64


class ImageHelper:
    @staticmethod
    def encode(img_uri: str):
        with open(img_uri, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    @staticmethod
    def get_default_org_logo():
        return ImageHelper.encode("helper/media/image/resources/happyface_logo.jpg")
