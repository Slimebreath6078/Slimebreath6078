from codecs import utf_32_encode, utf_8_encode
from encodings import utf_8, utf_8_sig
from os import write
from tkinter.filedialog import Open
import markdown
import os
import sys
import re
import collections


class SBMDSyntaxError(Exception):

    def __init__(self, line: int, text: str):
        self.__text: str = text
        self.__line: int = line

    def __str__(self):
        if self.__line is not None:
            return "(line "+str(self.__line)+") " + self.__text
        return self.__text


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


def parse_md(text: str) -> str:
    syntax_list = re.split(r"([\{\}])", text)
    output: list[str] = []
    div_list: collections.deque[list[str]] = collections.deque()
    for i, syntax in enumerate(syntax_list):
        match syntax:
            case '{':
                names = re.search(r"(?<=\[).+?(?=\]$)", syntax_list[i-1])
                if names is None:
                    line_count = "".join(syntax_list[:i]).count("\n")+1
                    raise SBMDSyntaxError(line_count,
                                          "id or class name, in [], was not found in front of \{\}.")
                name_list = re.split(' *?,', names.group())
                div_attr = ""
                for name in name_list:
                    match name[0]:
                        case '.':
                            div_attr += " class=\""+name[1:]+"\""
                        case '#':
                            div_attr += " id=\""+name[1:]+"\""
                        case _:
                            line_count = "".join(
                                syntax_list[:i]).count('\n')+1
                            raise SBMDSyntaxError(line_count,
                                                  "[]{} can set only id or class.")
                if div_list:
                    div_list[-1][-1] = re.sub("\[.+?\]",
                                              "", div_list[-1][-1])
                else:
                    output[-1] = re.sub("\[.+?\]",
                                        "", output[-1])
                div_list.append(["<div"+div_attr+">\r\n"])
            case '}':
                div_list[-1].append("\r\n</div>")
                div_syntax_text = div_list.pop()
                div_syntax_content = markdown.markdown("".join(div_syntax_text[1:-1]),
                                                       extensions=['tables'])
                div_text = (
                    div_syntax_text[0]+"{}"+div_syntax_text[-1]).format(div_syntax_content)
                if div_list:
                    div_list[-1].append(div_text)
                else:
                    output.append(div_text)
                    continue
            case _:
                if div_list:
                    div_list[-1].append(syntax)
                    output.append("")
                    continue
                output.append(syntax)
                continue
        output.append("")
    return "".join(output)


for cur_dir, dummy, file_list in markdown_path:
    for file_name in file_list:
        with open(os.path.join(cur_dir, file_name), 'r', encoding='utf_8_sig') as file:
            text = file.read()
            if ".md" in file_name:
                output_path = OutputPath(root_path, cur_dir, file_name)
                output_path.make_dir()
                print("Generating", str(output_path) + "...")
                text = parse_md(text)
                html = markdown.markdown(text, extensions=['tables'])
                output = "{}".format(html)
                with open(str(output_path), 'w', encoding='utf_8') as output_file:
                    output_file.writelines(output)
