import sys
import os
import re
sys.path.append("../base/")
from parse_sql import CSqlParse
from string_tools import CStringTools


class CWriteBase(object):
	def __init__(self, parser):
		self.m_parser = parser

	def define_name(self):
		return ""

	def include_sys_list(self):
		return []

	def include_other_list(self):
		return []

	def namespace(self):
		return ""

	def class_name(self):
		return ""

	def get_input_class_name(self, func_name, method_info):
		in_class = method_info.get(CSqlParse.IN_CLASS)
		name = ""
		if in_class is not None:
			name = in_class
		else:
			name = func_name
		# hump_func_name = CStringTools.underling2HumpLarger(func_name)
		hump_func_name = CStringTools.upperFirstByte(name)
		input_name = "C{0}Input".format(hump_func_name)
		return input_name

	def get_output_class_name(self, func_name, method_info):
		out_class = method_info.get(CSqlParse.OUT_CLASS)
		name = ""
		if out_class is not None:
			name = out_class
		else:
			name = func_name
		# hump_func_name = CStringTools.underling2HumpLarger(func_name)
		hump_func_name = CStringTools.upperFirstByte(name)
		output_name = "C{0}Output".format(hump_func_name)
		return output_name

	def get_method_param_list(self, method_info, method_param_list, param_no):
		func_name = method_info.get(CSqlParse.FUNC_NAME)
		sub_func_list = method_info.get(CSqlParse.SUB_FUNC_SORT_LIST)
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		def inner(method_param_list, param_no):
			input_name = self.get_input_class_name(func_name, method_info)
			output_name = self.get_output_class_name(func_name, method_info)
			in_isarr = method_info.get(CSqlParse.IN_ISARR)
			out_isarr = method_info.get(CSqlParse.OUT_ISARR)
			in_ismul = None
			out_ismul = None
			if in_isarr == "true":
				in_ismul = True
			else:
				in_ismul = False
			if out_isarr == "true":
				out_ismul = True
			else:
				out_ismul = False
			input_params_len = 0
			output_params_len = 0
			if input_params is not None:
				input_params_len = len(input_params)
			if output_params is not None:
				output_params_len = len(output_params)
			input_str = input_name
			output_str = output_name
			if in_ismul is True:
				input_str = "std::list<{0}>".format(input_name)
			if out_ismul is True:
				output_str = "std::list<{0}>".format(output_name)
			if input_params_len == 0 and output_params_len == 0:
				method_param_list += ""
			elif input_params_len > 0 and output_params_len == 0:
				method_param_list += "const {0} &input{1}".format(input_str, param_no)
			elif input_params_len == 0 and output_params_len > 0:
				method_param_list += "{0} &output{1}".format(output_str, param_no)
			elif input_params_len > 0 and output_params_len > 0:
				method_param_list += "const {0} &input{2}, {1} &output{2}".format(input_str, output_str, param_no)
			else:
				return None
			param_no += 1
			return method_param_list, param_no
		if sub_func_list is None:
			method_param_list, param_no = inner(method_param_list, param_no)
		else:
			i = 0
			length = len(sub_func_list)
			for sub_func_name, sub_func_index in sub_func_list:
				i += 1
				if func_name == sub_func_name:
					method_param_list, param_no = inner(method_param_list, param_no)
					if i < length and (input_params is not None or output_params is not None):
						method_param_list += ", "
					continue
				method = self.m_parser.get_methodinfo_by_methodname(sub_func_name)
				method_param_list, param_no = self.get_method_param_list(method, method_param_list, param_no)
				if i < length and (input_params is not None or output_params is not None):
					if (method.get(CSqlParse.INPUT_PARAMS) is not None and len(method.get(CSqlParse.INPUT_PARAMS)) > 0) or (method.get(CSqlParse.OUTPUT_PARAMS) is not None and len(method.get(CSqlParse.OUTPUT_PARAMS)) > 0):
						method_param_list += ", "
		return method_param_list, param_no

	def __sub_func_index_change(self, sub_func_index):
		if sub_func_index == "":
			return ""
		result = ""
		if int(sub_func_index) < 0:
			result = "N" + str(int(sub_func_index) * -1)
		elif int(sub_func_index) > 0:
			result = "P" + sub_func_index
		else:
			result = "0"
		return result

	def write_member_var(self, param_type, param_name):
		content = ""
		param_type = self.type_change(param_type)
		content += "{0} {1};".format(param_type, param_name)
		return content

	def write_get_method(self, param_type, param_name):
		content = ""
		param_type = self.type_change(param_type)
		content += "const {0} &get{1}() const".format(param_type, CStringTools.upperFirstByte(param_name))
		content += " { return this->" + param_name + "; }"
		return content

	def write_set_method(self, param_type, param_name):
		content = ""
		param_type = self.type_change(param_type)
		content += "void set{0}(const {1} &{2}, bool use = true)".format(CStringTools.upperFirstByte(param_name), param_type, param_name)
		content += " { this->" + "{0} = {0};".format(param_name) + " this->" + "{0}Used = use;".format(param_name) + " }"
		return content

	def write_construction_param(self, param_type, param_name):
		content = ""
		if param_type is None or param_name is None:
			return content
		param_type = self.type_change(param_type)
		content += "const {0} &{1}".format(param_type, param_name)
		return content

	def write_method_define(self, method_info):
		content = ""
		func_name = method_info.get(CSqlParse.FUNC_NAME)
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		sub_func_sort_list = method_info.get(CSqlParse.SUB_FUNC_SORT_LIST)
		bref = method_info.get(CSqlParse.BREF)
		if bref is not None:
			content += "\t"*1 + "// " + bref + "\n"
		c, _ = self.get_method_param_list(method_info, "", 0)
		if input_params is None and output_params is None and sub_func_sort_list is None:
			content += "\t"*1 + "uint32_t {0}(bool isAlreayStartTrans = false, sql::IConnect *reuseConn = nullptr, std::string *outSql = nullptr);\n".format(func_name)
		else:
			if c == "":
				content += "\t"*1 + "uint32_t {0}(bool isAlreayStartTrans = false, sql::IConnect *reuseConn = nullptr, std::string *outSql = nullptr);\n".format(func_name)
			else:
				content += "\t"*1 + "uint32_t {0}({1}, bool isAlreayStartTrans = false, sql::IConnect *reuseConn = nullptr, std::string *outSql = nullptr);\n".format(func_name, c)
		return content

	def write_method_implement(self, method_info):
		content = ""
		func_name = method_info.get(CSqlParse.FUNC_NAME)
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		is_start_trans = method_info.get(CSqlParse.IS_START_TRANS)
		sub_func_sort_list = method_info.get(CSqlParse.SUB_FUNC_SORT_LIST)
		# if output_params is not None:
		# 	out_isarr = method_info.get(CSqlParse.OUT_ISARR)
		# 	content += self.__write_callback(func_name, out_isarr, output_params)
		c, _ = self.get_method_param_list(method_info, "", 0)
		if input_params is None and output_params is None and sub_func_sort_list is None:
			content += "uint32_t {0}::{1}(bool isAlreayStartTrans /* = false */, sql::IConnect *reuseConn /* = nullptr*/, std::string *outSql /* = nullptr*/)\n".format(self.class_name(), func_name)
		else:
			if c == "":
				content += "uint32_t {0}::{1}(bool isAlreayStartTrans /* = false */, sql::IConnect *reuseConn /* = nullptr*/, std::string *outSql /* = nullptr*/)\n".format(self.class_name(), func_name)
			else:
				content += "uint32_t {0}::{1}({2}, bool isAlreayStartTrans /* = false */, sql::IConnect *reuseConn /* = nullptr*/, std::string *outSql /* = nullptr*/)\n".format(self.class_name(), func_name, c)
		content += "{\n"
		content += self.__write_execute(func_name, method_info)
		content += "\n"
		if is_start_trans is True:
			content += "\t"*1 + 'if (!isAlreayStartTrans) {\n'
			content += "\t"*2 + 'if (result) {\n'
			content += "\t"*3 + 'trans->commit();\n'
			# content += "\t"*3 + 'return 0;\n'
			content += "\t"*2 + '}\n'
			content += "\t"*2 + 'else {\n'
			content += "\t"*3 + 'trans->rollback();\n'
			# content += "\t"*3 + 'return 1;\n'
			content += "\t"*2 + '}\n'
			content += "\t"*2 + 'm_connPool.freeConnect(conn);\n'
			content += "\t"*1 + '}\n'
		content += "\n"
		content += "\t"*1 + "if (!result) {\n"
		content += "\t"*2 + "ret = 1;\n"
		content += "\t"*1 + "}\n"
		content += "\n"
		content += "\t"*1 + "return ret;\n"
		content += "}\n"
		content += "\n"
		return content

	def __read_data(self, func_name, output_params, isarr, method_info, n, param_no):
		content = ""
		var_type = self.get_output_class_name(func_name, method_info)
		output_params_len = len(output_params)
		content += "\t"*n + "std::vector<std::string> cols;\n"
		content += "\t"*n + "cols.resize({0});\n".format(str(output_params_len))
		content += "\t"*n + "bool b = row->scan(cols);\n"
		content += "\t"*n + "if (!b) continue;\n"
		if isarr is True:
			content += "\t"*n + "{0} tmp;\n".format(var_type)
		content += "\t"*n + "std::stringstream ss;\n"
		tmp = "output{0}.".format(param_no)
		if isarr is True:
			tmp = "tmp."
		i = 0
		for param in output_params:
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			if param_type is None or param_name is None:
				continue
			value = "cols[{0}]".format(i)
			param_type = self.type_change(param_type)
			if param_type != "std::string":
				content += "\t"*n + "{0} {1} = 0;\n".format(param_type, param_name)
				content += "\t"*n + "ss << cols[{0}];\n".format(i)
				content += "\t"*n + "ss >> {0};\n".format(param_name)
				content += "\t"*n + 'ss.clear();\n'
				value = param_name
			content += "\t"*n + "{0}set{1}({2});\n".format(tmp, CStringTools.upperFirstByte(param_name), value)
			i += 1
		if isarr is True:
			# content += "\t"*1 + "}\n"
			content += "\t"*n + "output{0}.push_back(tmp);\n".format(param_no)
		return content

	def __write_execute(self, func_name, method_info):
		in_isarr = method_info.get(CSqlParse.IN_ISARR)
		n = 1
		if in_isarr == "true":
			n = 2
		content = ""
		is_start_trans = method_info.get(CSqlParse.IS_START_TRANS)
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		content += "\t"*1 + 'uint32_t ret = 0;\n\n'
		content += "\t"*1 + 'sql::IConnect *conn = nullptr;\n'
		content += "\t"*1 + 'sql::ITransaction *trans = nullptr;\n'
		content += "\t"*1 + 'sql::IRow *row = nullptr;\n'
		content += "\t"*1 + 'bool result = true;\n'
		content += "\t"*1 + 'std::string sql("");\n'
		content += "\t"*1 + 'if (!isAlreayStartTrans) {\n'
		content += "\t"*2 + 'conn = m_connPool.connect(m_dial);\n'
		content += "\t"*2 + 'if (conn == nullptr) return -1;\n'
		if is_start_trans is True:
			content += "\t"*2 + 'trans = conn->begin();\n'
			content += "\t"*2 + 'if (trans == nullptr) {\n'
			content += "\t"*3 + 'm_connPool.freeConnect(conn);\n'
			content += "\t"*3 + 'return -1;\n'
			content += "\t"*2 + '}\n'
		content += "\t"*1 + '}\n'
		if input_params is not None:
			content += "\t"*1 + 'else {\n'
			content += "\t"*2 + 'conn = reuseConn;\n'
			content += "\t"*1 + '}\n'
			content += "\t"*1 + "std::stringstream ss;\n"
		sub_func_sort_list = method_info.get(CSqlParse.SUB_FUNC_SORT_LIST)
		c, _ = self.__write_input(method_info, "", 0)
		content += c
		"""
		if input_params is not None:
			if is_start_trans is True:
				content += "\t"*1 + 'if (!isAlreayStartTrans) {\n'
				content += "\t"*2 + 'if (result) {\n'
				content += "\t"*3 + 'trans->commit();\n'
				content += "\t"*3 + 'return 0;\n'
				content += "\t"*2 + '}\n'
				content += "\t"*2 + 'else {\n'
				content += "\t"*3 + 'trans->rollback();\n'
				content += "\t"*3 + 'return 1;\n'
				content += "\t"*2 + '}\n'
				content += "\t"*2 + 'm_connPool.freeConnect(conn);\n'
				content += "\t"*1 + '}\n'
		"""
		return content

	def __write_input(self, method_info, content, param_no):
		func_name = method_info.get(CSqlParse.FUNC_NAME)
		in_isarr = method_info.get(CSqlParse.IN_ISARR)
		is_start_trans = method_info.get(CSqlParse.IS_START_TRANS)
		if in_isarr is None:
			raise SystemExit("[Keyword Error] (function {0}) in_isarr is exist".format(func_name))
		out_isarr = method_info.get(CSqlParse.OUT_ISARR)
		if out_isarr is None:
			raise SystemExit("[Keyword Error] (function {0}) out_isarr is exist".format(func_name))
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		buf_len = method_info.get(CSqlParse.BUFLEN)
		if buf_len is None:
			buf_len = "512"
		is_brace = method_info.get(CSqlParse.IS_BRACE)
		if is_brace is None:
			is_brace = False
		is_group = method_info.get(CSqlParse.IS_GROUP)
		n = 1
		if in_isarr == "true":
			n = 2
		sub_func_list = method_info.get(CSqlParse.SUB_FUNC_SORT_LIST)
		def judge_result():
			content = ""
			if is_start_trans is True:
				content += "\t"*1 + 'if (!isAlreayStartTrans) {\n'
				content += "\t"*2 + 'if (result) {\n'
				content += "\t"*3 + 'trans->commit();\n'
				# content += "\t"*3 + 'return 0;\n'
				content += "\t"*2 + '}\n'
				content += "\t"*2 + 'else {\n'
				content += "\t"*3 + 'trans->rollback();\n'
				# content += "\t"*3 + 'return 1;\n'
				content += "\t"*2 + '}\n'
				content += "\t"*2 + 'm_connPool.freeConnect(conn);\n'
				content += "\t"*1 + '}\n'
			return content
		def inner(content, param_no):
			sql = method_info.get(CSqlParse.SQL)
			if sql is None:
				sql = ""
			sql = re.sub(r"\n", "\n\t\t", sql)
			if input_params is not None:
				if in_isarr == "true":
					content += "\t"*1 + "for (auto iter = input{0}.begin(); iter != input{0}.end(); ++iter)\n".format(param_no)
					content += "\t"*1 + "{\n"
				if is_group is None or is_group is False:
					if is_brace is False:
						content += "\t"*n + self.__replace_sql_by_input_params(input_params, in_isarr, sql, param_no, False)
					else:
						sql, fulls = self.__replace_sql_brace(input_params, in_isarr, sql, param_no, False)
						content += '\t'*n + 'ss << "' + sql
				else:
					content += self.__write_group(func_name, method_info, in_isarr, is_brace, input_params, sql, param_no, n)
				content += "\t"*n + 'sql = ss.str();\n'
				content += "\t"*n + 'if (outSql != nullptr) *outSql = sql;\n'
				content += "\t"*n + 'ss.str("");\n'
			else:
				content += "\t"*1 + 'sql = "{0}";\n'.format(sql)
			if output_params is None:
				content += "\t"*n + 'result = conn->exec(sql);\n'
				if in_isarr == "true":
					content += "\t"*n + 'if (!result) break;\n'
			else:
				content += "\t"*n + 'row = conn->query(sql, result);\n'
				content += "\t"*n + 'if (result == true && row != nullptr) {\n'
				# content += "\t"*n + 'if (result == false) {\n'
				# content += "\t"*(n+1) + 'if (trans != nullptr) trans->rollback();\n'
				# content += "\t"*(n+1) + 'm_connPool.freeConnect(conn);\n'
				# content += "\t"*(n+1) + 'return -1;\n'
				# content += "\t"*n + '}\n'
				# content += "\t"*n + 'if (result == true && row == nullptr) {\n'
				# content += "\t"*(n+1) + 'if (trans != nullptr) trans->commit();\n'
				# content += "\t"*(n+1) + 'm_connPool.freeConnect(conn);\n'
				# content += "\t"*(n+1) + 'return 0;\n'
				# content += "\t"*n + '}\n'
				var_type = self.get_output_class_name(func_name, method_info)
				# if out_isarr == "true":
				# 	content += "\t"*(n+1) + "output{0}.clear();\n".format(param_no)
				content += "\t"*(n+1) + 'while (row->next()) {\n'
				isarr = False
				if out_isarr == "true":
					isarr = True
				content += self.__read_data(func_name, output_params, isarr, method_info, n+2, param_no)
				content += "\t"*(n+1) + '}\n'
				content += "\t"*(n+1) + 'row->close();\n'
				content += "\t"*n + '}\n'
			if in_isarr == "true":
				content += "\t"*1 + "}\n"
			# content += judge_result()
			param_no += 1
			return content, param_no
		if sub_func_list is None:
			content, param_no = inner(content, param_no)
		else:
			for sub_func_name, sub_func_index in sub_func_list:
				if func_name == sub_func_name:
					content, param_no = inner(content, param_no)
					continue
				method = self.m_parser.get_methodinfo_by_methodname(sub_func_name)
				content, param_no = self.__write_input(method, content, param_no)
		return content, param_no

	def __write_group(self, func_name, method_info, in_isarr, is_brace, input_params, sql, param_no, n):
		content = ""
		# write implement
		sql_group_info = method_info.get(CSqlParse.SQL_GROUP_INFO)
		sql_group_list = sql_group_info.get(CSqlParse.SQL_GROUP_LIST)
		group_input_params = method_info.get(CSqlParse.GROUP_INPUT_PARAMS)
		sql_group_list_len = len(sql_group_list)
		group_input_params_len = len(group_input_params)
		if sql_group_list_len != group_input_params_len:
			raise SystemExit("[Match Error] func_name: {0}".format(func_name))
		groups = CStringTools.binary_bit_combination(sql_group_list_len)
		j = 0
		for group in groups:
			j += 1
			if j == 1:
				content += "\t"*n + "if ("
			else:
				content += "\n" + "\t"*n + "else if ("
			i = 0
			group_len = len(group)
			sql_tmp = sql
			sql_tmp = re.sub(r"\/\*begin\{\d?\}\*\/", "", sql_tmp)
			sql_tmp = re.sub(r"\/\*end\*\/", "", sql_tmp)
			sql_tmp = re.sub(r"[ ]{2,}?", " ", sql_tmp)
			for item in group:
				i += 1
				t_f = ""
				if item == 0:
					t_f = "false"
					# replace
					group_no, group_field = sql_group_list[i - 1]
					index = sql_tmp.index(group_field)
					pre = sql_tmp[index - 4:index].strip()
					if pre == "and":
						sql_tmp = self.__replace_substring_by_pos(sql_tmp, index - 4, index, "")
					size = len(group_field)
					index = sql_tmp.index(group_field)
					back = sql_tmp[index + size:index + size + 4].strip()
					if back == "and":
						sql_tmp = self.__replace_substring_by_pos(sql_tmp, index + size, index + size + 4, "")
					sql_tmp = sql_tmp.replace(group_field, "")
				else:
					t_f = "true"
				this_field = "input{0}.".format(param_no)
				if in_isarr == "true":
					this_field = "iter->"
				content += "{0}get{1}Used() == {2}".format(this_field, CStringTools.upperFirstByte(group_input_params[i - 1].get(CSqlParse.PARAM_NAME)), t_f)
				if i < group_len:
					content += " && "
			if 1 not in group:
				sql_tmp = re.sub("where", "", sql_tmp)

			tmp = ""
			if is_brace is True:
				sql_tmp, fulls = self.__replace_sql_brace(input_params, in_isarr, sql_tmp, param_no, True)
				tmp += '\t'*(n+1) + 'ss << "' + sql_tmp
				"""
				sql_tmp, fulls = self.__replace_sql_brace(input_params, in_isarr, sql_tmp, True)
				tmp += "\t"*(n+1) + 'snprintf(buf, sizeof(buf), "{0}"'.format(sql_tmp)
				if len(fulls) > 0:
					tmp += "\n" + "\t"*(n+2) + ", "
				tmp += self.__get_input_brace_posture(in_isarr, input_params, fulls)
				tmp += ");"
				"""
			else:
				tmp += "\t"*(n+1) + self.__replace_sql_by_input_params(input_params, in_isarr, sql_tmp, True)
				"""
				tmp += "\t"*(n+1) + 'snprintf(buf, sizeof(buf), "{0}"'.format(self.__replace_sql_by_input_params(input_params, sql_tmp, True))
				if len(fulls) > 0:
					tmp += "\n" + "\t"*(n+2) + ", "
				tmp += self.__get_input_posture(in_isarr, input_params)
				tmp += ");"
				"""

			content += ") {\n" + "{0}".format(tmp) + "\t"*n + "}"
		content += "\n"
		return content

	def __replace_substring_by_pos(self, src, begin, end, s):
		li = []
		i = 0
		for item in src:
			if i >= begin and i < end:
				li.append(s)
			else:
				li.append(item)
			i += 1
		return "".join(li)

	def __get_input_posture_single(self, in_isarr, input_param, param_no):
		content = ""
		preix = "input{0}.".format(param_no)
		if in_isarr == "true":
			preix = "iter->"
		param_name = input_param.get(CSqlParse.PARAM_NAME)
		param_type = input_param.get(CSqlParse.PARAM_TYPE)
		content += "{0}get{1}()".format(preix, CStringTools.upperFirstByte(param_name))
		if param_type == "string":
			content += ".c_str()"
		return content

	def __get_input_posture(self, in_isarr, input_params, param_no):
		content = ""
		length = len(input_params)
		i = 0
		preix = "input{0}.".format(param_no)
		if in_isarr == "true":
			preix = "iter->"
		for param in input_params:
			i += 1
			param_name = param.get(CSqlParse.PARAM_NAME)
			param_type = param.get(CSqlParse.PARAM_TYPE)
			content += "{0}get{1}()".format(preix, CStringTools.upperFirstByte(param_name))
			if param_type == "string":
				content += ".c_str()"
			if i < length:
				content += ", "
		return content

	def __get_input_brace_posture(self, in_isarr, input_params, fulls):
		content = ""
		length = len(fulls)
		i = 0
		preix = "input."
		if in_isarr == "true":
			preix = "iter->"
		for number, keyword, last_is_other, next_is_other in fulls:
			i += 1
			param = input_params[number]
			param_name = param.get(CSqlParse.PARAM_NAME)
			param_type = param.get(CSqlParse.PARAM_TYPE)
			content += "{0}get{1}()".format(preix, CStringTools.upperFirstByte(param_name))
			if param_type == "string":
				content += ".c_str()"
			if i < length:
				content += ", "
		return content

	def __replace_sql_brace(self, input_params, in_isarr, sql, param_no, is_group):
		fulls, max_number = CStringTools.get_brace_format_list2(sql)
		param_len = len(input_params)
		full_set = set(fulls)
		full_len = len(full_set)
		if is_group is False:
			if param_len != full_len:
				str_tmp = "[Param Length Error] may be last #define error ? fulllen length({1}) != params length({2})\n[sql] : \t{0}".format(sql, full_len, param_len)
				raise SystemExit(str_tmp)
			if param_len < max_number + 1:
				str_tmp = "[Param Match Error] may be last #define error ? input param length == {1}, max index == {2}\n[sql] : \t{0}".format(sql, param_len, max_number)
				raise SystemExit(str_tmp)
		for number, keyword, last_is_other, next_is_other in list(full_set):
			inpams = input_params[number]
			tmp = ""
			if last_is_other is True:
				tmp += '"'
			if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
				tmp += """ << "'" << """
			else:
				tmp += " << "
			value = self.__get_input_posture_single(in_isarr, inpams, param_no)
			tmp += value
			if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
				tmp += """ << "'" << """
			else:
				tmp += " << "
			if next_is_other is True:
				tmp += '"'
			sql = re.sub(keyword, tmp, sql)
		sql += '";\n'
		return sql, fulls

	def __replace_sql_by_input_params(self, input_params, in_isarr, sql, param_no, is_group):
		content = 'ss << "'
		param_len = len(input_params)
		symbol_len = len(re.findall(r"\?", sql))
		if is_group is False:
			if param_len != symbol_len:
				str_tmp = "[Param Length Error] may be last #define error ? symbol length({1}) != params length({2})\n[sql] : \t{0}".format(sql, symbol_len, param_len)
				raise SystemExit(str_tmp)
		i = 0
		last_isnot_symbol = True
		last_is_symbol = False
		for ch in sql:
			if ch == "?":
				if last_isnot_symbol is True:
					content += '"'
					last_isnot_symbol = False
				inpams = input_params[i]
				value = self.__get_input_posture_single(in_isarr, inpams, param_no)
				if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
					content += ' << "\\"" << '
				else:
					content += " << "
				content += '{0}'.format(value)
				if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
					content += ' << "\\"" << '
				else:
					content += " << "
				i += 1
				last_is_symbol = True
			else:
				if last_is_symbol is True:
					content += '"'
					last_is_symbol = False
				content += ch
				last_isnot_symbol = True
		# find {0} {1} ...
		content += '";\n'
		return content

	def write_construction_param_list(self, param_list):
		content = ""
		length = len(param_list)
		i = 0
		for param in param_list:
			i += 1
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			content += self.write_construction_param(param_type, param_name)
			if i < length:
				content += ", "
		return content

	def write_default_init_param_list(self, param_list):
		return self.__write_init_param_list(param_list, True)

	def write_member_init_param_list(self, param_list):
		return self.__write_init_param_list(param_list, False)

	def write_init_param(self, param_type, param_name, is_default):
		content = ""
		if param_type is None or param_name is None:
			return content
		param_type = self.type_change(param_type)
		value = param_name
		if param_type == "std::string":
			if is_default is True:
				value = '""'
		else:
			if is_default is True:
				value = "0"
		content += "{0}({1})".format(param_name, value)
		return content

	def __write_init_param_list(self, param_list, is_default):
		content = ""
		length = len(param_list)
		i = 0
		for param in param_list:
			i += 1
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			content += self.write_init_param(param_type, param_name, is_default)
			if i < length:
				content += ", "
		return content

	def write_header(self):
		content = ""
		content += "#ifndef {0}\n".format(self.define_name())
		content += "#define {0}\n".format(self.define_name())
		content += "\n"
		return content

	def write_includes(self):
		content = ""
		for include in self.include_sys_list():
			content += '#include <{0}>\n'.format(include)
		for include in self.include_other_list():
			content += '#include "{0}"\n'.format(include)
		content += "\n"
		return content

	def write_namespace_define(self):
		content = ""
		content += "namespace {0}\n".format(self.namespace())
		content += "{\n"
		content += "\n"
		return content

	def write_namespace_end(self):
		content = ""
		content += "}\n"
		content += "\n"
		return content

	def write_class_define(self):
		content = ""
		content += "class {0}\n".format(self.class_name())
		content += "{\n"
		return content

	def write_class_end(self):
		content = ""
		content += "};\n"
		content += "\n"
		return content

	def write_tail(self):
		content = ""
		content += "#endif // {0}\n".format(self.define_name())
		return content

	def type2symbol(self, param_type):
		symbol = ""
		if param_type == "string":
			symbol = "%s"
		elif param_type == "bool":
			symbol = "%d"
		elif param_type == "int8":
			symbol = "%c"
		elif param_type == "uint8":
			symbol = "%u"
		elif param_type == "int16":
			symbol = "%hd"
		elif param_type == "uint16":
			symbol = "%u"
		elif param_type == "int":
			symbol = "%d"
		elif param_type == "uint":
			symbol = "%u"
		elif param_type == "int32":
			symbol = "%d"
		elif param_type == "uint32":
			symbol = "%u"
		elif param_type == "int64":
			symbol = "%lld"
		elif param_type == "uint64":
			symbol = "%llu"
		elif param_type == "float":
			symbol = "%f"
		elif param_type == "double":
			symbol = "%lf"
		return symbol

	def type_change(self, param_type):
		if param_type == "string":
			param_type = "std::string"
		if param_type == "int8":
			param_type = "char"
		if param_type == "uint8":
			param_type = "unsigned char"
		if param_type == "int16":
			param_type = "short"
		if param_type == "uint16":
			param_type = "unsigned short"
		if param_type == "int32":
			param_type = "int"
		if param_type == "uint32":
			param_type = "unsigned"
		if param_type == "uint":
			param_type = "unsigned"
		if param_type == "int64":
			param_type = "long long"
		if param_type == "uint64":
			param_type = "unsigned long long"
		if param_type == "float32":
			param_type = "float"
		if param_type == "float64":
			param_type = "double"
		return param_type
