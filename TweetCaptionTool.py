
import Global
import Helper
from ApiController import ApiController
from CaptionController import CaptionController

if __name__ == "__main__":
    Helper.Log('Starting Tweet Caption Tool...')

    Global.init()

    apiController = ApiController()
    apiController.startListen()
    apiController.startTrans()

    captionController = CaptionController()
    captionController.waitTask()
