# encoding=utf8
import sys
import os
sys.path.append("../base")
import re
from string_tools import CStringTools
from file_handle_re import CFileHandle
from parse_sql import CSqlParse
from write_base import CWriteBase


class CWriteSqliteImpCpp(CWriteBase):
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
		self.m_file_path = os.path.join(root, filename + "_db_handler.cpp")

	def define_name(self):
		return "__{0}_DB_HANDLER_H__".format(self.m_namespace.upper())

	def include_sys_list(self):
		return ["stdio.h", "string.h", "sstream"]

	def include_other_list(self):
		return ["sqlite3.h", self.m_file_name + "_db_handler.h"]

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
		# content += self.write_header()
		content += self.write_includes()
		content += self.write_namespace_define()
		# content += self.write_class_define()
		content += self.__write_implement(info_dict)
		# content += self.write_class_end()
		content += self.write_namespace_end()
		# content += self.write_tail()
		self.m_content += content
		# print(self.m_content)
		self.m_file_handler.clear_write(self.m_content, self.m_file_path, "utf8")

	def __write_implement(self, info_dict):
		create_tables_sql = info_dict.get(CSqlParse.CREATE_TABELS_SQL)
		content = ""
		content += "{0}::{0}(const std::string &dbpath, bool isMemory)\n".format(self.class_name())
		content += "\t"*1 + ": m_db(nullptr)\n"
		content += "\t"*1 + ", m_mutex()\n"
		content += "{\n"
		content += "\t"*1 + "sqlite3_threadsafe();\n"
		content += "\t"*1 + "sqlite3_config(SQLITE_CONFIG_MULTITHREAD);\n"
		content += "\t"*1 + "int ret = SQLITE_OK;\n"
		content += "\t"*1 + "if (isMemory == false) {\n"
		content += "\t"*2 + "ret = sqlite3_open(dbpath.c_str(), &m_db);\n"
		content += "\t"*1 + "}\n"
		content += "\t"*1 + "else {\n"
		content += "\t"*2 + 'ret = sqlite3_open(":memory:", &m_db);\n'
		content += "\t"*1 + "}\n"
		if create_tables_sql is not None:
			content += "\t"*1 + "if (ret == SQLITE_OK) {\n"
			content += "\t"*2 + 'std::string sql = "\\\n{0}";\n'.format(create_tables_sql)
			content += "\t"*2 + "sqlite3_exec(m_db, sql.c_str(), nullptr, nullptr, nullptr);\n"
			content += "\t"*1 + "}\n"
		content += "}\n"
		content += "\n"
		content += "{0}::~{0}()\n".format(self.class_name())
		content += "{\n"
		content += "\t"*1 + "sqlite3_close(m_db);\n"
		content += "}\n"
		method_list = info_dict.get(CSqlParse.METHOD_LIST)
		content += self.__write_methods(method_list)
		return content

	def __write_methods(self, method_list):
		content = ""
		content += "\n"
		for method_info in method_list:
			content += self.write_method_implement(method_info)
		content += "/*@@start@@*/" + "\n\n"
		return content


if __name__ == "__main__":
	parser = CSqlParse("./example_sql/user_info.sql")
	parser.read()
	info_dict = parser.get_info_dict()
	writer = CWriteSqliteImpCpp(parser.get_file_path(), root="./obj")
	writer.write(info_dict)
