from codecs import utf_32_encode, utf_8_encode
from encodings import utf_8, utf_8_sig
from os import write
from tkinter.filedialog import Open
import markdown
import os
import sys
import re


class OutputPath:
    def __init__(self, root=str(), cur_dir=str(), file_name=str()):
        self.__root = root
        self.__dir = str()
        self.__file_name = str()
        m_dir = re.findall(r".*?_docs[\\/]*(.*)$", cur_dir)
        m_file = re.findall(r"(.+)\.md", file_name)
        if bool(m_dir):
            self.__dir = m_dir[0]
        else:
            self.__dir = ""
        if bool(m_file):
            self.__file_name = m_file[0] + ".html"
        else:
            self.__file_name = ""

    def __str__(self) -> str:
        if self.__dir == "":
            os.path.join(self.__root, "_html", self.__file_name)
        return os.path.join(self.__root, "_html", self.__dir, self.__file_name)

    def make_dir(self):
        if self.__dir == "":
            return
        dir = os.path.join(self.__root, "_html", self.__dir)
        os.makedirs(dir, exist_ok=True)


root_path = sys.argv[1]
markdown_path = os.walk(root_path + "_docs")

for cur_dir, dummy, file_list in markdown_path:
    for file_name in file_list:
        # print(os.path.join(cur_dir, file_name))
        with open(os.path.join(cur_dir, file_name), 'r', encoding='utf_8_sig') as file:
            text = file.read()
            if ".md" in file_name:
                html = markdown.markdown(text)
                output = "{}".format(html)
                # print(output)
                output_path = OutputPath(root_path, cur_dir, file_name)
                print("Generating", str(output_path) + "...")
                output_path.make_dir()
                with open(str(output_path), 'w', encoding='utf_8') as output_file:
                    output_file.writelines(output)
