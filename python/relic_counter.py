# python -m pip install maafw
import os
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from maa.context import Context
from maa.resource import Resource
from maa.controller import AdbController
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.notification_handler import NotificationHandler, NotificationType

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def cv2AddChineseText(img, text, position, textColor, textSize):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype(
        "simsun.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


import json

# for register decorator
resource = Resource()


def main():
    user_path = "./"
    resource_path = "assets/resource"

    Toolkit.init_option(user_path)

    res_job = resource.post_bundle(resource_path)
    res_job.wait()
    
    # If not found on Windows, try running as administrator
    adb_devices = Toolkit.find_adb_devices()
    if not adb_devices:
        print("No ADB device found.")
        exit()

    # for demo, we just use the first device
    device = adb_devices[0]
    controller = AdbController(
        adb_path=device.adb_path,
        address=device.address,
        screencap_methods=device.screencap_methods,
        input_methods=device.input_methods,
        config=device.config,
    )
    controller.post_connection().wait()

    tasker = Tasker()
    # tasker = Tasker(notification_handler=MyNotificationHandler())
    tasker.bind(resource, controller)

    if not tasker.inited:
        print("Failed to init MAA.")
        exit()

    # just an example, use it in json
    pipeline_override = {
        "藏品识别": {"action": "custom", "custom_action": "RelicRecognition"},
    }

    # another way to register
    # resource.register_custom_recognition("My_Recongition", MyRecongition())
    # resource.register_custom_action("My_CustomAction", MyCustomAction())

    task_detail = tasker.post_task("藏品识别", pipeline_override).wait().get()
    # do something with task_detail
    print("task_detail:", task_detail)


# auto register by decorator, can also call `resource.register_custom_action` manually
@resource.custom_action("RelicRecognition")
class RelicRecognition(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。-参考流水线协议 `on_error`
        """
        print(f"on RelicRecognition.run, context: {context}, argv: {argv}")

        # context.override_next(argv.node_name, ["TaskA", "TaskB"])

        image = context.tasker.controller.cached_image
        image_copy = image.copy()
        # context.tasker.controller.post_click(100, 100).wait()

        relics_path = os.path.join("assets/resource", "image/relics")

        with open('python/roguelike_topic_table.json', "r") as f:
            relics = json.load(f)['details']['rogue_4']['items']

        relic_list = []

        for relic_file in os.listdir(relics_path):
            reco_detail = context.run_recognition(
                "Relic", image, {"Relic": {"recognition": "FeatureMatch", 
                                           "template": "relics/"+relic_file,
                                           "ordered_by": "Score"},
                                           "roi": [
                                                322,
                                                152,
                                                725,
                                                500
                                            ]}
            )
            if reco_detail is not None:
                print(reco_detail)
                w, h = reco_detail.box.w, reco_detail.box.h
                if w > 90 or h > 90:
                    continue
                relic_name = relics[relic_file.split('.')[0]]['name']
                relic_list.append(relic_name)
                # draw rectangle
                cv2.rectangle(image_copy, (reco_detail.box.x, reco_detail.box.y), 
                              (reco_detail.box.x + w, reco_detail.box.y + h), (0, 255, 0), 2)
                # add text
                image_copy = cv2AddChineseText(image_copy, relic_name, (reco_detail.box.x, reco_detail.box.y), (0, 255, 0), 12)
        
        # save copy image
        cv2.imwrite("relics_recognition.jpg", image_copy)

        print(relic_list)
        print("nums:", len(relic_list))

        return CustomAction.RunResult(success=True)


if __name__ == "__main__":
    main()