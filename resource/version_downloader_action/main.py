# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/21


import pprint
import re
import os
import sys
import _thread
import shutil
import codecs

from Qt import QtWidgets
from Qt import QtCore
import ftrack_api

import ui


class Version(object):
    def __init__(self, version_entity):
        # 版本实体
        self.version_entity = version_entity
        self.version_name = ""
        self.main_paths = []
        self.fullres_path = ""
        self.info = ""

        self.build_data()

    def get_fullres_path(self):
        """
        通过提交的 main_paths, 找到对应的 fullers path
        """
        for p in self.main_paths:
            for path_part in p.split("/"):
                # 匹配到版本号部分的路径
                re_match = re.match("[v|V]\d+", path_part)
                if re_match:
                    v_path = p.split(re_match.group())[0] + "%s" % re_match.group()
                    # 组合 fullres 路径
                    fullres_path = v_path + "/fullres"
                    if os.path.isdir(fullres_path):
                        self.fullres_path = fullres_path

    def get_main_path(self):
        """
        从组件中获取 main 路径
        """
        components_collection = self.version_entity.get("components")
        if not components_collection:
            return

        for c in components_collection:
            if not c:
                continue
            if c.get("name") == "main":
                for location in c.get("component_locations"):
                    p = location.get("resource_identifier")
                    p = p.replace("\\", "/")
                    self.main_paths.append(p)

    def combination_version_name(self):
        """
        通过 version link version名
        version_link: []
        """
        version_name_parts = []
        link = self.version_entity.get("_link", [])
        if not link:
            return

        for vl in link:
            # 加上project部分的命名就太长了
            if vl.get("type") == "Project":
                continue
            version_name_parts.append(vl.get("name", ""))

        if version_name_parts:
            self.version_name = "_".join(version_name_parts)

    def build_data(self):
        # 通过 link 数据拼接版本名
        self.combination_version_name()
        if not self.version_name:
            self.info = u"没有找到版本文件"
            return

        # 获取主组件路径
        self.get_main_path()
        if not self.main_paths:
            self.info = u"版本没有提交主路径"
            return

        # 解析 fullres 路径
        self.get_fullres_path()
        if not self.fullres_path:
            self.info = u"版本没有 fullres 路径"


class Response(ui.MainUI):
    instance = None
    setconnect = QtCore.Signal(str)

    def __init__(self, list_entity):
        super(Response, self).__init__()
        # 列表实例
        self.list_entity = list_entity
        # 列表名
        self.list_name = list_entity.get("name")
        # 版本集合
        self.versions_entity = ()
        # 日志文件路径
        self.log_file = ""

        self.__setup_data()
        self.__set_content()

    def __setup_data(self):
        # 将 list 名作为工具名
        self.set_titile(self.list_name)

    def __set_content(self):
        self.download_button.clicked.connect(self.__download_thread)
        self.setconnect.connect(self.add_content)

    def copy_files(self, src_path, dst_path):
        status = True
        for fd in os.listdir(src_path):
            f = os.path.join(src_path, fd)
            if os.path.isfile(f):
                base_name = os.path.basename(f)
                try:
                    shutil.copy2(f, dst_path)
                    self.do_verbose(u"%s: %s" % (base_name, u"导出成功"))
                except Exception as e:
                    status = False
                    self.do_verbose(u"%s: %s" % (base_name, e), log=True)
        return status

    def get_output_path(self):
        output_path = self.output_lineedit.text()
        if os.path.isdir(output_path):
            return output_path.replace("\\", "/")

    def __download_thread(self):
        _thread.start_new_thread(self.download, ())

    def do_verbose(self, content, log=False):
        self.setconnect.emit(content)
        if log and self.log_file:
            # 写入拷贝日志
            with codecs.open(self.log_file, "a+", "utf-8") as f:
                f.write(u"%s\n" % content)

    def download(self):
        # 获取输出路径
        ouput_path = self.get_output_path()
        if not ouput_path:
            self.do_verbose(u"输出路径不正确")
            return

        # 生成输出日志文件路径
        self.log_file = os.path.join(ouput_path, u"%s_导出日志.txt" % self.list_name)
        # 删除旧日志
        if os.path.isfile(self.log_file):
            try:
                os.remove(self.log_file)
            except:
                pass

        self.do_verbose(u"正在导出列表 %s" % self.list_name)

        # 获取版本实体
        self.versions_entity = self.list_entity.get("items", ())
        if len(self.versions_entity) == 0:
            self.do_verbose(u"没有找到版本文件")
            return

        # 设置进度条范围
        self.dl_progressbar.setRange(0, len(self.versions_entity))

        # 从版本实体中获取每个版本
        progressbar_value = 1
        for v_entity in self.versions_entity:
            # 进度条进 1
            self.dl_progressbar.setValue(progressbar_value)
            progressbar_value += 1

            if not v_entity:
                continue

            ver = Version(v_entity)
            # 显示当前导出版本名
            self.do_verbose(u"[%s]" % ver.version_name, log=True)

            if not ver.fullres_path:
                self.do_verbose(u"%s\n" % ver.info, log=True)
                continue

            # 创建下载文件夹
            download_path = os.path.join(ouput_path, ver.version_name)
            if not os.path.exists(download_path):
                try:
                    os.makedirs(download_path)
                except Exception as e:
                    self.do_verbose(u"创建文件夹目录失败：%s" % download_path, log=True)
                    self.do_verbose(u"%s\n" % str(e), log=True)
                    continue

            # 执行文件拷贝
            if self.copy_files(ver.fullres_path, download_path):
                self.do_verbose(u"完成\n", log=True)
            else:
                self.do_verbose(u"失败\n", log=True)

        self.do_verbose(u"结束\n")
        try:
            os.startfile(self.log_file)
        except:
            pass


def get_list_entity(server_url, api_key, api_user, list_id):
    session = ftrack_api.Session(server_url=server_url,
                                 api_key=api_key,
                                 api_user=api_user)

    return session.query("List where id is {}".format(list_id)).first()


def load_ui(list_entity):
    app = QtWidgets.QApplication(sys.argv)
    VD = Response(list_entity)
    VD.show()
    VD.raise_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    server_url = sys.argv[1]
    api_user = sys.argv[2]
    api_key = sys.argv[3]
    list_id = sys.argv[4]
    # 获取列表实体
    list_entity = get_list_entity(server_url, api_key, api_user, list_id)
    # 启动ui
    load_ui(list_entity)


    # import aut
    #
    # server_url = aut.server_url
    # api_key = aut.api_key
    # api_user = aut.api_user
    #
    # list_id = u"466c7786-cd30-11eb-96f2-246e961667ed"

    # versions_entity = list_entity.get("items", ())
    # for versions_entity in versions_entity:
    #     v = Version(versions_entity)
    #     print(v.version_name)
    #     print(v.main_paths)
    #     print(v.fullres_path)
    #     print(v.info)

    #load_ui(server_url, api_key, api_user, list_id)
