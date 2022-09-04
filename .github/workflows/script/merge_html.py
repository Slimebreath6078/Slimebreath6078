from encodings import utf_8_sig
import os
from secrets import token_bytes
import sys
import re
import enum
from tkinter import INSERT


root_path = sys.argv[1]
output_path = sys.argv[2]
markdown_path = os.walk(root_path + "_html")


class MergerSyntaxError(Exception):
    def __init__(self, text=""):
        self.__text = text

    def __str__(self):
        return "Html merger syntax error:" + self.__text


class HtmlToken(enum.Enum):
    INSERT_MARKDOWN = 0
    ENDIF = 1
    JUDGE_SYMBOL = 2
    REPLACE_CONST = 3
    INSERT_TEMPLATE = 4
    INSERT_STYLE = 5


class DefineData:
    def __init__(self):
        self.__symbol_list: list[str] = []
        self.__style_list: list[str] = []
        self.__const_list: dict = {}
        self.__title: str
        self.__template_html: str

    def add_symbol(self, word: str):
        self.__symbol_list.append(word)
        self.__symbol_list = sorted(self.__symbol_list)

    def add_style(self, word: str):
        self.__style_list.append(word)
        self.__style_list = sorted(self.__style_list)

    def add_const_list(self, name: str, value: str):
        self.__const_list[name] = value

    def set_template_html(self, template_html: str):
        self.__template_html = template_html

    def set_title(self, title: str):
        self.__title = title

    def symbol_defined(self, word: str) -> bool:
        return word in self.__symbol_list

    def get_style_list(self) -> list[str]:
        return self.__style_list

    def get_template_html(self) -> str:
        return self.__template_html

    def get_title(self) -> str:
        return self.__title

    def get_const(self, name: str) -> str:
        if name in self.__const_list:
            return self.__const_list[name]
        return ""


def analyse_define_token(define_data: DefineData, token_list: list[str]):
    match token_list[0]:
        case "def":
            match token_list[1]:
                case "symbol":
                    define_data.add_symbol(token_list[2])
                case "const":
                    define_data.add_const_list(token_list[2], token_list[3])
        case "template_html":
            define_data.set_template_html(token_list[1])
        case "style":
            define_data.add_style(token_list[1])


def parse_html_token(token_list: list[str]) -> tuple[HtmlToken, list[str]]:
    match token_list[0][0]:
        case '$':
            return HtmlToken.REPLACE_CONST, token_list[0][1:]
        case _:
            match token_list[0]:
                case "MARKDOWN":
                    return HtmlToken.INSERT_MARKDOWN, ""
                case "ENDIF":
                    return HtmlToken.ENDIF, ""
                case "SYMBOL":
                    return HtmlToken.JUDGE_SYMBOL, token_list[1]
                case "TEMPLATE":
                    return HtmlToken.INSERT_TEMPLATE, token_list[1]
                case "STYLE":
                    return HtmlToken.INSERT_STYLE, ""


def parse_define_file(define_file: str) -> DefineData:
    define_data = DefineData()
    with open(define_file, 'r', encoding='utf_8_sig') as file:
        text = file.readlines()
        for line in text:
            analyse_define_token(define_data, re.split('[ \n]', line))
    return define_data


def merge_html(cur_dir: str, file_name: str, define_data: DefineData) -> list[str]:
    file_path = os.path.join(cur_dir, file_name)
    template_path = define_data.get_template_html()
    output_text: list[str] = []
    output_directory = re.sub(
        os.path.join(root_path, "_html") + r"\\?", "", cur_dir)
    with open(os.path.join(root_path, "_template", template_path), 'r', encoding='utf_8') as f:
        flag_list: list[bool] = []
        text = f.readlines()
        for line in text:
            tabs = re.match("[\t ]*", line).group()
            find: list[str] = re.findall("\{.*?\}", line)
            output_line = line
            if find.count == 0:
                continue
            for syntax in find:
                token_list = syntax[1:-1].split(' ')
                token_result = parse_html_token(token_list)
                if False in flag_list and token_result[0] != HtmlToken.ENDIF:
                    line.replace(syntax, "")
                    continue
                match token_result[0]:
                    case HtmlToken.INSERT_MARKDOWN:
                        with open(file_path, 'r', encoding='utf_8') as file_html:
                            replace_text_base = file_html.readlines()
                            replace_text = ""
                            for i, replace_line in enumerate(replace_text_base):
                                if i == 0:
                                    replace_text = replace_text + replace_line
                                else:
                                    replace_text = replace_text + tabs + replace_line
                            output_line = output_line.replace(
                                syntax, replace_text)
                    case HtmlToken.INSERT_TEMPLATE:
                        with open(os.path.join(root_path, "_template", token_result[1]), 'r') as find_template:
                            replace_text_base = find_template.readlines()
                            replace_text: str()
                            for i, replace_line in enumerate(replace_text_base):
                                if i == 0:
                                    replace_text = replace_text + replace_line
                                else:
                                    replace_text = replace_text + tabs + replace_line
                            output_line = output_line.replace(
                                syntax, '\n'.join(replace_text))
                    case HtmlToken.INSERT_STYLE:
                        replace_text = ""
                        for i, style in enumerate(define_data.get_style_list()):
                            if i == 0:
                                replace_text = replace_text + "<link rel=\"stylesheet\" href=\"style/" + \
                                    style + "\" type=\"text/css\">"
                            else:
                                replace_text = '\n' + tabs + replace_text + \
                                    "<link rel=\"stylesheet\" href=\"style/" + style + "\" type=\"text/css\">"
                        output_line = output_line.replace(
                            syntax, replace_text)
                    case HtmlToken.JUDGE_SYMBOL:
                        flag_list.append(
                            define_data.symbol_defined(token_result[1]))
                        output_line = output_line.replace(syntax, '')
                    case HtmlToken.REPLACE_CONST:
                        output_line = output_line.replace(
                            syntax, define_data.get_const(token_result[1]))
                    case HtmlToken.ENDIF:
                        del (flag_list[-1])
                        output_line = output_line.replace(syntax, '')
                    case _:
                        raise MergerSyntaxError("illegal command")
            if not False in flag_list:
                if bool(re.search(("[^ \t\n^]+"), output_line)) == True:
                    output_text.append(output_line)
    if output_directory != "":
        os.makedirs(os.path.join(output_path, output_directory), exist_ok=True)
    with open(os.path.join(output_path, output_directory, file_name), 'w', encoding='utf_8') as f:
        f.writelines(output_text)
    print("Completed", "->", os.path.join(output_path, output_directory, file_name))


default_define_data = parse_define_file(os.path.join(root_path, "default.def"))

for cur_dir, dummy, file_list in markdown_path:
    for file_name in file_list:
        if ".html" in file_name:
            define_data: DefineData
            define_file = os.path.join(
                root_path, "_docs", str(re.match("(.+)\.html", file_name)) + ".def")
            if define_file in file_list:
                define_data = parse_define_file(define_file)
            else:
                define_data = default_define_data
            print("Merging", file_name + "...")
            text = merge_html(cur_dir, file_name, define_data)
