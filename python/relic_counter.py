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
        # context.tasker.controller.post_click(100, 100).wait()

        relics_path = os.path.join("assets/resource", "image/relics")
        for relic_file in os.listdir(relics_path):
            reco_detail = context.run_recognition(
                "Relic", image, {"Relic": {"recognition": "FeatureMatch", "template": "relics/"+relic_file}}
            )
            if reco_detail is not None:
                print(reco_detail)

        return CustomAction.RunResult(success=True)


if __name__ == "__main__":
    main()