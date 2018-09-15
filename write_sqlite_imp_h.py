# encoding=utf8
import sys
import os
sys.path.append("../base")
import re
from string_tools import CStringTools
from file_handle_re import CFileHandle
from parse_sql import CSqlParse
from write_base import CWriteBase


class CWriteSqliteImpH(CWriteBase):
	def __init__(self, file_path, root="."):
		self.m_file_handler = CFileHandle()
		self.m_file_name = ""
		self.m_file_path = ""
		self.m_content = ""
		self.m_namespace = ""
		self.__compare_file_path(file_path, root)

	def __compare_file_path(self, file_path, root):
		basename = os.path.basename(file_path)
		filename, fileext = os.path.splitext(basename)
		self.m_file_name = filename
		self.m_file_path = os.path.join(root, filename + "_db_handler.h")

	def define_name(self):
		return "__{0}_DB_HANDLER_H__".format(self.m_namespace.upper())

	def include_sys_list(self):
		return ["stdint.h", "mutex"]

	def include_other_list(self):
		return ["{0}_db_param.h".format(self.m_file_name)]

	def namespace(self):
		return self.m_namespace

	def class_name(self):
		return "CDbHandler"

	def write(self, info_dict):
		# 获取 namesapce
		namespace = info_dict.get(CSqlParse.NAMESPACE)
		if namespace is None or namespace == "":
			raise RuntimeError("namespace is empty")
		self.m_namespace = namespace
		content = ""
		content += self.write_header()
		content += self.write_includes()
		content += "struct sqlite3;\n"
		content += self.write_namespace_define()
		content += self.write_class_define()
		content += self.__write_implement(info_dict)
		content += self.write_class_end()
		content += self.write_namespace_end()
		content += self.write_tail()
		self.m_content += content
		# print(self.m_content)
		self.m_file_handler.clear_write(self.m_content, self.m_file_path, "utf8")

	def __write_implement(self, info_dict):
		content = ""
		content += "public:\n"
		content += "\t"*1 + "explicit {0}(const std::string &dbpath, bool isMemory = false);\n".format(self.class_name())
		content += "\t"*1 + "virtual ~{0}();\n".format(self.class_name())
		method_list = info_dict.get(CSqlParse.METHOD_LIST)
		content += self.__write_methods(method_list)
		content += self.__write_private_member()
		return content

	def __write_methods(self, method_list):
		content = ""
		content += "\n"
		content += "public:\n"
		content += "\t"*1 + "/*@@start@@*/" + "\n"
		for method_info in method_list:
			content += self.write_method_define(method_info)
		return content

	def __write_private_member(self):
		content = ""
		content += "\n"
		content += "private:\n"
		content += "\t"*1 + "sqlite3 *m_db;\n"
		content += "\t"*1 + "std::mutex m_mutex;\n"
		return content


if __name__ == "__main__":
	parser = CSqlParse("./file/user_info.sql")
	parser.read()
	info_dict = parser.get_info_dict()
	writer = CWriteSqliteImpH(parser.get_file_path(), root="./obj")
	writer.write(info_dict)
