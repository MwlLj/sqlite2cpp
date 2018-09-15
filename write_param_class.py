# encoding=utf8
import sys
import os
sys.path.append("../base")
import re
from string_tools import CStringTools
from file_handle_re import CFileHandle
from parse_sql import CSqlParse
from write_base import CWriteBase


class CWriteParamClass(CWriteBase):
	def __init__(self, file_path, root="."):
		self.m_file_handler = CFileHandle()
		self.m_file_path = ""
		self.m_content = ""
		self.m_namespace = ""
		self.m_import_list = []
		self.__compare_file_path(file_path, root)

	def __compare_file_path(self, file_path, root):
		basename = os.path.basename(file_path)
		filename, fileext = os.path.splitext(basename)
		self.m_file_path = os.path.join(root, filename + "_db_param.h")

	def define_name(self):
		return "__{0}_DB_PARAM_H__".format(self.m_namespace.upper())

	def include_sys_list(self):
		return ["string", "list"]

	def include_other_list(self):
		paths = []
		for path in self.m_import_list:
			path = re.sub(r'"', "", path);
			paths.append(path)
		return paths

	def namespace(self):
		return self.m_namespace

	def class_name(self):
		return "CDbParam"

	def write(self, info_dict):
		# 获取 namesapce
		namespace = info_dict.get(CSqlParse.NAMESPACE)
		if namespace is None or namespace == "":
			raise RuntimeError("namespace is empty")
		self.m_namespace = namespace
		self.m_import_list = info_dict.get(CSqlParse.IMPORT_LIST)
		content = ""
		content += self.write_header()
		content += self.write_includes()
		content += self.write_namespace_define()
		# content += self.write_class_define()
		content += self.__write_implement(info_dict)
		# content += self.write_class_end()
		content += self.write_namespace_end()
		content += self.write_tail()
		self.m_content += content
		# print(self.m_content)
		self.m_file_handler.clear_write(self.m_content, self.m_file_path, "utf8")

	def __write_implement(self, info_dict):
		content = ""
		method_list = info_dict.get(CSqlParse.METHOD_LIST)
		for method_info in method_list:
			func_name = method_info.get(CSqlParse.FUNC_NAME)
			input_params = method_info.get(CSqlParse.INPUT_PARAMS)
			output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
			if input_params is not None:
				content += self.__write_class(func_name, input_params, True)
			if output_params is not None:
				content += self.__write_class(func_name, output_params, False)
		return content

	def __write_class(self, func_name, param_list, is_input):
		content = ""
		class_name = ""
		if is_input is True:
			class_name = self.get_input_class_name(func_name)
		else:
			class_name = self.get_output_class_name(func_name)
		content += "class {0}\n".format(class_name)
		content += "{\n"
		content += "public:\n"
		content += "\t"*1 + "explicit {0}()\n".format(class_name)
		content += "\t"*2 + ": {0}".format(self.write_default_init_param_list(param_list)) + " {}\n"
		content += "\t"*1 + "explicit {0}({1})\n".format(class_name, self.write_construction_param_list(param_list))
		content += "\t"*2 + ": {0}".format(self.write_member_init_param_list(param_list)) + " {}\n"
		content += "\t"*1 + "virtual ~{0}()".format(class_name) + " {}\n"
		content += self.__write_methods(param_list)
		content += self.__write_private_member(param_list)
		content += "};\n"
		content += "\n"
		return content

	def __write_methods(self, param_list):
		content = ""
		content += "\n"
		content += "public:\n"
		for param in param_list:
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			if param_type is None or param_name is None:
				continue
			content += "\t"*1 + self.write_set_method(param_type, param_name) + "\n"
			content += "\t"*1 + self.write_get_method(param_type, param_name) + "\n"
			content += "\t"*1 + self.write_get_method("bool", param_name + "Used") + "\n"
		return content

	def __write_private_member(self, param_list):
		content = ""
		content += "\n"
		content += "private:\n"
		for param in param_list:
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			if param_type is None or param_name is None:
				continue
			content += "\t"*1 + self.write_member_var(param_type, param_name) + "\n"
			content += "\t"*1 + self.write_member_var("bool", param_name + "Used") + "\n"
		return content


if __name__ == "__main__":
	parser = CSqlParse("./file/user_info.sql")
	parser.read()
	info_dict = parser.get_info_dict()
	writer = CWriteParamClass(parser.get_file_path(), root="./obj")
	writer.write(info_dict)
