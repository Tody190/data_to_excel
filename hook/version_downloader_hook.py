# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/08


import os
import pprint
import sys
import argparse

import logging
import ftrack_api
import subprocess


IDENTIFIER = "versiondownloader-launch-action"
APP_NAME = u"版本文件下载"

RESOURCE_FOLDER = "version_downloader_action"
RESOURCE_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "resource", RESOURCE_FOLDER)
)

if RESOURCE_DIRECTORY not in sys.path:
    sys.path.append(RESOURCE_DIRECTORY)



class VersionDownloader(object):
    identifier = IDENTIFIER

    def __init__(self):
        super(VersionDownloader, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # 此 action 必须包含一个标识符（identifier）
        if self.identifier is None:
            raise ValueError('The action must be given an identifier.')

    def register(self, session):
        # Ftrack 的会话实例
        self.session = session
        # Ftrack api用户
        self.api_user = self.session.api_user

        # region subscribe(subscription, callback, subscriber=None, priority=100)
        # 用于指定回调函数事件
        # subscription：特定字符串名详细指定回调事件名
        # callback：指定的回调函数
        # subscriber：
        # priority： 优先级，0最高，100最低
        # endregion

        # region 订阅一个 discover 方法，用来在控件上显示启动按钮
        # event
        # Event(
        #     topic='ftrack.action.discover',
        #     data=dict(
        #         selection=[
        #             dict(
        #                 entityId='eb16970c-5fc6-11e2-bb9a-f23c91df25eb',
        #                 entityType='task',
        #             )
        #         ]
        #     )
        # )
        # reply data
        # dict(
        #     items=[
        #         dict(
        #             label='Mega Modeling',
        #             variant='2014',
        #             actionIdentifier='ftrack-connect-launch-applications-action',
        #             icon='URL to custom icon or predefined name',
        #             applicationIdentifier='mega_modeling_2014'
        #         ),
        #         dict(
        #             label='Professional Painter',
        #             icon='URL to custom icon or predefined name',
        #             actionIdentifier='ftrack-connect-launch-applications-action',
        #             applicationIdentifier='professional_painter'
        #         ),
        #         dict(
        #             label='Cool Compositor',
        #             variant='v2',
        #             actionIdentifier='ftrack-connect-launch-applications-action'
        #         icon = 'URL to custom icon or predefined name',
        #                applicationIdentifier = 'cc_v2',
        #                                        cc_plugins = ['foo', 'bar']
        # )
        # ]
        # )
        # endregion
        session.event_hub.subscribe(
            "topic=ftrack.action.discover and source.user.username={0}".format(
                self.api_user),
            self.discover
        )

        # region 订阅一个 action.launch 方法，用来启动应用
        # event
        # Event(
        #     topic='ftrack.action.launch',
        #     data=dict(
        #         actionIdentifier='ftrack-connect-launch-applications-action',
        #         applicationIdentifier='maya-2014',
        #         foo='bar',
        #         selection=[
        #             dict(
        #                 entityId='eb16970c-5fc6-11e2-bb9a-f23c91df25eb',
        #                 entityType='task'
        #             )
        #         ]
        #     )
        # )
        # reply data
        # dict(
        #     success=True,
        #     message='maya-2014 launched successfully.'
        # )
        # endregion
        session.event_hub.subscribe(
            "topic=ftrack.action.launch and data.actionIdentifier={0}".format(
                self.identifier),
            self.launch
        )

    def discover(self, event):
        # 只有当前操作的用户是当前事件发出的用户时才启动
        if self.session.api_user != event["source"]["user"]["username"]:
            return
        # 选中实体时才能使用
        if not event["data"].get("selection"):
            return

        # 选中的实体是 list 才启用
        selection = event["data"]["selection"]
        if selection:
            entity_type = selection[0]["entityType"]
            if entity_type != u"list":
                return
        else:
            return

        # print("discover" + "-" * 20)
        # print("discover" + "-" * 20)

        return {
            'items': [{
                'label': APP_NAME,
                'actionIdentifier': self.identifier,
                'icon': 'default'
            }]
        }

    def launch(self, event):
        # 只有当前操作的用户是当前事件发出的用户时才启动
        if self.session.api_user != event["source"]["user"]["username"]:
            return
        # 通过标识符判断启动的是不是当前实例
        if event["data"]["actionIdentifier"] != self.identifier:
            return

        print("launch" + "-" * 20)
        server_url = self.session.server_url
        api_user = self.session.api_user
        api_key = self.session.api_key
        list_id = event["data"]["selection"][0]["entityId"]
        commands = ["python27",
                    "%s/main.py" % RESOURCE_DIRECTORY,
                    server_url,
                    api_user,
                    api_key,
                    list_id]
        subprocess.Popen(commands, shell=True)
        print("-" * 20)

        return {
            'success': True,
            'message': u'启动...'
        }


def register(session, **kw):
    if not isinstance(session, ftrack_api.Session):
        return
    action = VersionDownloader()
    action.register(session)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
            logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v', '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='info'
    )
    namespace = parser.parse_args()

    # Set up basic logging
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    # 保护认证信息
    try:
        import aut
        server_url = aut.server_url
        api_key = aut.api_key
        api_user = aut.api_user
    except:
        raise

    session = ftrack_api.Session(server_url=server_url,
                                 api_key=api_key,
                                 api_user=api_user,
                                 auto_connect_event_hub=True)

    register(session)

    '''Wait for events.'''
    session.event_hub.wait()
