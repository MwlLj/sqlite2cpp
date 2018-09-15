# encoding=utf8
import sys
import os
sys.path.append("../base")
import re
from string_tools import CStringTools
from parse_sql import CSqlParse
from update_base import CUpdateBase
from write_base import CWriteBase

class CUpdateSqliteImpCpp(CUpdateBase, CWriteBase):
	def __init__(self, file_path):
		CUpdateBase.__init__(self, file_path)
		self.m_content = ""
		self.m_namespace = ""
		self.m_info_dict = {}
		
	def full_content(self, content):
		self.m_content = content

	def start_keys(self):
		return [r"/\*@@start@@\*/"]

	def seekout(self, key):
		content = ""
		if key == r"/\*@@start@@\*/":
			content += self.__get_content()
		return content

	def is_debug(self):
		return False

	def update(self, info_dict):
		self.m_info_dict = info_dict
		self.m_namespace = info_dict.get(CSqlParse.NAMESPACE)
		self.read()

	def namespace(self):
		return self.m_namespace

	def class_name(self):
		return "CDbHandler"

	def __get_content(self):
		content = ""
		method_list = self.m_info_dict.get(CSqlParse.METHOD_LIST)
		for method_info in method_list:
			func_name = method_info.get(CSqlParse.FUNC_NAME)
			define = "uint32_t {0}::{1}({2})".format(self.class_name(), func_name, self.get_method_param_list(func_name, method_info))
			is_exist = CStringTools.is_exist(r'(?:^|[ |\s]*?){0}'.format(CStringTools.filter_reg_keyword(define)), self.m_content)
			if is_exist is False:
				content += self.write_method_implement(method_info)
		return content


if __name__ == '__main__':
	parse = CSqlParse("./file/user_info.sql")
	parse.read()
	info_dict = parse.get_info_dict()
	update = CUpdateSqliteImpCpp("./obj/user_info_db_handler.cpp")
	update.update(info_dict)
