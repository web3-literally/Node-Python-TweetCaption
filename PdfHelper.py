from PIL import Image

class PdfHelper():
    def __init__(self):
        super().__init__()
        self.DPI = 96
        self.MM_IN_INCH = 25.4
        self.A4_WIDTH = 350
        self.A4_HEIGHT = 500
        self.MAX_WIDTH = 1250
        self.MAX_HEIGHT = 1850

    def pixelsToMM(self, pixel):
        return pixel * self.MM_IN_INCH / self.DPI

    def resizeToFit(self, imageFileName):
        im = Image.open(imageFileName)
        width, height = im.size
        widthScale = self.MAX_WIDTH / width
        heightScale = self.MAX_HEIGHT / height
        scale = min(widthScale, heightScale)
        return (
            round(self.pixelsToMM(scale * width)),
            round(self.pixelsToMM(scale * height))
        )

    def centreImage(self, pdf, imageFileName):
        width, height = self.resizeToFit(imageFileName)
        pdf.image(imageFileName, (self.A4_WIDTH - width) / 2,
                   (self.A4_HEIGHT - height) / 2,
                   width, height)

