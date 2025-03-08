# python -m pip install maafw
import os
import json

from maa.tasker import Tasker
from maa.toolkit import Toolkit
from maa.context import Context
from maa.resource import Resource
from maa.controller import AdbController
from maa.custom_action import CustomAction

import cv2
import time 
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class RougeTopic:
    def __init__(self, topic, font_color):
        self.topic = topic
        self.relics = []
        self.font_color = font_color

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

def preprocess_image(img, base_color):
    # return img
    print(base_color)
    # 转换为HSV颜色空间（更易分离颜色）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 定义字体颜色
    lower_color = np.array([base_color - 1, 50, 50])
    upper_color = np.array([base_color + 1, 255, 255]) 
    
    # 创建颜色掩膜
    mask = cv2.inRange(hsv, lower_color, upper_color)
    
    # # 形态学操作（去除噪点）
    # kernel = np.ones((2,2), np.uint8)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # # 增强对比度（CLAHE算法）
    # lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    # l, a, b = cv2.split(lab)
    # clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    # l_clahe = clahe.apply(l)
    # lab_clahe = cv2.merge((l_clahe,a,b))
    # enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    
    # 应用颜色掩膜到增强后的图像
    result = cv2.bitwise_and(hsv, hsv, mask=mask)
    
    # # 转换为灰度图并进行自适应阈值处理
    # gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    # thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #                               cv2.THRESH_BINARY,11,2)
    
    # # 最终处理：反转颜色（白底黑字更易识别）
    # final = cv2.bitwise_not(thresh)
    
    return result

# for register decorator
resource = Resource()

def pi_cli_run():
    Toolkit.pi_register_custom_action("RelicRecognition", RelicRecognition())
    Toolkit.pi_run_cli("./assets", "./", False)

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
        "藏品识别": {"action": "custom", "custom_action": "RelicRecognition", "custom_action_param": {
            "topic": "rogue_4"
        }},
    }

    # relics_path = os.path.join("assets/resource", "image/relics")

    # pull up 
    # for _ in range(5):
    #     tasker.controller.post_swipe(1245,50,1245,600,30).wait()
    #     time.sleep(2)

# auto register by decorator, can also call `resource.register_custom_action` manually
@resource.custom_action("RelicRecognition")
class RelicRecognition(CustomAction):
    table_path = os.path.join("resource/data", "roguelike_topic_table.json")
    relic_names = {}
    if not os.path.exists(table_path):
        raise FileNotFoundError("roguelike_topic_table.json not found.")
    with open(table_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
        for topic in ["rogue_1", "rogue_2", "rogue_3", "rogue_4"]:
            relics = json_data['details'][topic]['items']
            relic_names[topic] = [relic['name'] for relic in relics.values() if relic['type'] == 'RELIC']
    
    def __init__(self):
        self.all_relics = []
        self._handle = self._c_run_agent

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
        self.all_relics = []
        # print(argv.custom_action_param)
        topic = json.loads(argv.custom_action_param)['topic']
        if topic not in ["rogue_1", "rogue_2", "rogue_3", "rogue_4"]:
            raise ValueError("Invalid topic.")
        
        base_color = 20 if topic == "rogue_1" else 90

        nums = 0

        while True:
            image = context.tasker.controller.post_screencap().wait().get()
            image_copy = image.copy()
            image = preprocess_image(image, base_color)
            # cv2.imwrite("debug/" + "filterd" + ".jpg", image)
            reco_detail = context.run_recognition(
                "Relic", image, {"Relic": {
                "recognition": "OCR",
                "expected": "[\\u4e00-\\u9fa5]+",
                "roi": [69,0,1144,631]
                }}
            )
            if reco_detail is None:
                print("total relics:", len(self.all_relics))
                print("No new relics found, stop.")
                break
            cv2.imwrite("debug/" + "filterd" + str(reco_detail.reco_id) + ".jpg", image)
            # context.tasker.controller.post_click(100, 100).wait()

            relic_list = [] # 识别到的藏品列表

            # print(reco_detail.all_results)

            for all in reco_detail.all_results:
                text = all.text
                if(text == ''):
                    continue
                print(text)
                if (text[-1]=='a' or text[-1]=='A'):
                    text = text[:-1]+'α'
                if (text[-1]=='b' or text[-1]=='B'):
                    text = text[:-1]+'β'
                if (text[-1]=='y' or text[-1]=='Y'):
                    text = text[:-1]+'γ'
                if text in self.relic_names[topic]:
                    # print(text)
                    relic_list.append(text)
                    box = all.box
                    cv2.rectangle(image_copy, (box[0], box[1]), 
                                (box[0] + box[2], box[1] + box[3]), (0, 255, 0), 2)
                    image_copy = cv2AddChineseText(image_copy, text, (box[0], box[1] - 12), (0, 255, 0), 12)

            # for relic_file in os.listdir(relics_path):
            #     reco_detail = context.run_recognition(
            #         "Relic", image, {"Relic": {"recognition": "FeatureMatch", 
            #                                    "template": "relics/"+relic_file,
            #                                    "ordered_by": "Score"},
            #                                    "roi": [69,0,1144,631]
            #                                    }
            #     )
            #     if reco_detail is not None:
            #         print(reco_detail)
            #         w, h = reco_detail.box.w, reco_detail.box.h
            #         if w > 90 or h > 90:
            #             continue
            #         relic_name = relics[relic_file.split('.')[0]]['name']
            #         relic_list.append(relic_name)
            #         # draw rectangle
            #         cv2.rectangle(image_copy, (reco_detail.box.x, reco_detail.box.y), 
            #                       (reco_detail.box.x + w, reco_detail.box.y + h), (0, 255, 0), 2)
            #         # add text
            #         image_copy = cv2AddChineseText(image_copy, relic_name, (reco_detail.box.x, reco_detail.box.y), (0, 255, 0), 12)
            
            # save copy image

            cv2.imwrite("debug/" + "relics_recognition"+ str(reco_detail.reco_id) +".jpg", image_copy)

            print(relic_list)
            print("nums:", len(relic_list))     

            self.all_relics.extend(relic_list)
            self.all_relics = list(set(self.all_relics))
            if (nums == len(self.all_relics)):
                print("total relics:", len(self.all_relics))
                # print(self.all_relics)
                print("No new relics found, stop.")
                break
            nums = len(self.all_relics)
            context.tasker.controller.post_swipe(1245, 600, 1245, 450, 90).wait()
            time.sleep(1)
            context.tasker.controller.post_click(1245, 600).wait()

        print(self.all_relics)

        return CustomAction.RunResult(success=True)


if __name__ == "__main__":
    pi_cli_run()