# encoding=utf8
import sys
import os
import shutil
sys.path.append("../base")
from file_handle_re import CFileHandle
from cmdline_handle import CCmdlineHandle
from parse_sql import CSqlParse
from write_param_class import CWriteParamClass
from write_sqlite_imp_h import CWriteSqliteImpH
from write_sqlite_imp_cpp import CWriteSqliteImpCpp
from update_sqlite_imp_h import CUpdateSqliteImpH
from update_sqlite_imp_cpp import CUpdateSqliteImpCpp


class CCmdHandle(CCmdlineHandle):
	MODE_CREATE = 1
	MODE_UPDATE = 2
	def __init__(self):
		CCmdlineHandle.__init__(self)
		self.m_file_path = None
		self.m_obj = "."
		self.m_cpp_obj = None
		self.m_h_obj = None
		self.m_is_help = False
		self.m_mode = CCmdHandle.MODE_UPDATE

	def get_register_dict(self):
		return {"-f": 1, "-o": 1, "-co": 1, "-ho": 1, "-h": 0, "-create": 0, "-update": 0}

	def single_option(self, option, param_list):
		if option == "-h":
			self.m_is_help = True
			self.__print_help_info()
		elif option == "-f":
			file_path = param_list[0]
			self.m_file_path = file_path
		elif option == "-o":
			self.m_obj = param_list[0]
		elif option == "-co":
			self.m_cpp_obj = param_list[0]
		elif option == "-ho":
			self.m_h_obj = param_list[0]
		elif option == "-create":
			self.m_mode = CCmdHandle.MODE_CREATE
		elif option == "-update":
			self.m_mode = CCmdHandle.MODE_UPDATE

	def param_error(self, option):
		if option == "-f":
			print("please input filepath")
		elif option == "-o":
			print("please input objpath")
		elif option == "-co":
			print("please input objpath")
		elif option == "-ho":
			print("please input objpath")

	def __create_dirs(self, path):
		if os.path.exists(path) is False:
			os.makedirs(path)

	def parse_end(self):
		if self.m_is_help is True:
			return
		if self.m_file_path is None:
			print("please input filepath")
			return
		isExist = os.path.exists(self.m_file_path)
		if isExist is False:
			print("file is not exist")
			return
		# 判断输出目录是否存在
		obj_flag = False
		cpp_obj_flag = False
		h_obj_flag = False
		self.__create_dirs(self.m_obj)
		h_obj = self.m_obj
		if self.m_h_obj is not None:
			h_obj = self.m_h_obj
		self.__create_dirs(h_obj)
		cpp_obj = self.m_obj
		if self.m_cpp_obj is not None:
			cpp_obj = self.m_cpp_obj
		self.__create_dirs(cpp_obj)
		parser = CSqlParse(self.m_file_path)
		parser.read()
		info_dict = parser.get_info_dict()
		namespace = info_dict.get(CSqlParse.NAMESPACE)
		# 写参数类
		writer = CWriteParamClass(parser.get_file_path(), root=h_obj)
		writer.write(info_dict)
		if self.m_mode == CCmdHandle.MODE_UPDATE:
			# 更新实现的h文件
			basename = os.path.basename(self.m_file_path)
			imp_h_path = os.path.join(h_obj, "{0}_db_handler.h".format(namespace))
			if os.path.exists(imp_h_path) is False:
				raise RuntimeError(imp_h_path + "is not exist")
			imp_cpp_path = os.path.join(cpp_obj, "{0}_db_handler.cpp".format(namespace))
			if os.path.exists(imp_cpp_path) is False:
				raise RuntimeError(imp_cpp_path + "is not exist")
			updater = CUpdateSqliteImpH(imp_h_path)
			updater.update(info_dict)
			updater = CUpdateSqliteImpCpp(imp_cpp_path)
			updater.update(info_dict)
		elif self.m_mode == CCmdHandle.MODE_CREATE:
			# 写头文件
			writer = CWriteSqliteImpH(parser.get_file_path(), root=h_obj)
			writer.write(info_dict)
			# 写源文件
			writer = CWriteSqliteImpCpp(parser.get_file_path(), root=cpp_obj)
			writer.write(info_dict)

	def __print_help_info(self):
		info = "\n\toptions:\n"
		info += "\t\t-h: help\n"
		info += "\t\t-f: *.sql file path\n"
		info += "\t"*2 + "-o: output file path\n"
		info += "\t"*2 + "-ho: output .h file path\n"
		info += "\t"*2 + "-co: output .cpp file path\n"
		info += "\t"*2 + "-create: create files\n"
		info += "\t"*2 + "-update: update files\n"
		info += "\n" + "\t"*1 + "for example:\n"
		info += "\t"*2 + "python -create ./main.py -f ./file/xxx.sql -ho ./project/handler/include -co ./project/handler/source\n"
		info += "\t"*2 + "python -update ./main.py -f ./file/xxx.sql -ho ./project/handler/include -co ./project/handler/source\n"
		info += "\n"
		print(info)


if __name__ == "__main__":
	handle = CCmdHandle()
	handle.parse()
