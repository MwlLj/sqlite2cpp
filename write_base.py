import sys
import os
import re
sys.path.append("../base/")
from parse_sql import CSqlParse
from string_tools import CStringTools


class CWriteBase(object):
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

	def get_input_class_name(self, func_name):
		# hump_func_name = CStringTools.underling2HumpLarger(func_name)
		hump_func_name = CStringTools.upperFirstByte(func_name)
		input_name = "C{0}Input".format(hump_func_name)
		return input_name

	def get_output_class_name(self, func_name):
		# hump_func_name = CStringTools.underling2HumpLarger(func_name)
		hump_func_name = CStringTools.upperFirstByte(func_name)
		output_name = "C{0}Output".format(hump_func_name)
		return output_name

	def get_method_param_list(self, func_name, method_info):
		input_name = self.get_input_class_name(func_name)
		output_name = self.get_output_class_name(func_name)
		method_param_list = ""
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		in_isarr = method_info.get(CSqlParse.IN_ISARR)
		out_isarr = method_info.get(CSqlParse.OUT_ISARR)
		if input_params is None and output_params is None:
			method_param_list = ""
		elif input_params is not None and output_params is None:
			if in_isarr is not None and in_isarr == "true":
				method_param_list = "const std::list<{0}> &input".format(input_name)
			else:
				method_param_list = "const {0} &input".format(input_name)
		elif input_params is None and output_params is not None:
			if out_isarr is not None and out_isarr == "true":
				method_param_list = "std::list<{0}> &output".format(output_name)
			else:
				method_param_list = "{0} &output".format(output_name)
		else:
			in_template = ""
			out_template = ""
			if in_isarr is not None and in_isarr == "true":
				in_template = "const std::list<{0}> &input".format(input_name)
			else:
				in_template = "const {0} &input".format(input_name)
			if out_isarr is not None and out_isarr == "true":
				out_template = "std::list<{0}> &output".format(output_name)
			else:
				out_template = "{0} &output".format(output_name)
			method_param_list = in_template + ", " + out_template
		return method_param_list

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
		bref = method_info.get(CSqlParse.BREF)
		if bref is not None:
			content += "\t"*1 + "// " + bref + "\n"
		content += "\t"*1 + "uint32_t {0}({1});\n".format(func_name, self.get_method_param_list(func_name, method_info))
		return content

	def write_method_implement(self, method_info):
		content = ""
		func_name = method_info.get(CSqlParse.FUNC_NAME)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		if output_params is not None:
			out_isarr = method_info.get(CSqlParse.OUT_ISARR)
			content += self.__write_callback(func_name, out_isarr, output_params)
		content += "uint32_t {0}::{1}({2})\n".format(self.class_name(), func_name, self.get_method_param_list(func_name, method_info))
		content += "{\n"
		content += "\t"*1 + "if (m_db == nullptr) return -1;\n"
		content += "\t"*1 + "uint32_t ret = 0;\n"
		content += "\n"
		content += self.__write_execute(func_name, method_info)
		content += "\n"
		content += "\t"*1 + "return ret;\n"
		content += "}\n"
		content += "\n"
		return content

	def __write_callback(self, func_name, out_isarr, output_params):
		content = ""
		callback_name = func_name + "Callback"
		var_type = self.get_output_class_name(func_name)
		isarr = False
		if out_isarr is not None and out_isarr == "true":
			isarr = True
			var_type = "std::list<{0}>".format(var_type)
		content += "int {0}(void *data, int colCount, char **colValue, char **colName)\n".format(callback_name)
		content += "{\n"
		content += "\t"*1 + "int ret = 0;\n"
		content += "\n"
		content += "\t"*1 + "{0} *p = reinterpret_cast<{0}*>(data);\n".format(var_type)
		content += "\t"*1 + "if (p == nullptr) return -1;\n"
		tmp = "p->"
		tmp_len = 1
		if isarr is True:
			tmp = "tmp."
			tmp_len = 1
			content += "\t"*1 + "{0} tmp;\n".format(self.get_output_class_name(func_name))
			# content += "\t"*1 + "for (int i = 0; i < colCount; ++i)\n"
			# content += "\t"*1 + "{\n"
		i = 0
		content += "\t"*tmp_len + "std::stringstream ss;\n"
		for param in output_params:
			param_type = param.get(CSqlParse.PARAM_TYPE)
			param_name = param.get(CSqlParse.PARAM_NAME)
			if param_type is None or param_name is None:
				continue
			value = "colValue[{0}]".format(i)
			param_type = self.type_change(param_type)
			content += "\t"*tmp_len + "if (colValue[{0}] != nullptr) ".format(i) + "{\n"
			if param_type != "std::string":
				content += "\t"*(tmp_len+1) + "{0} {1} = 0;\n".format(param_type, param_name)
				content += "\t"*(tmp_len+1) + "ss << colValue[{0}];\n".format(i)
				content += "\t"*(tmp_len+1) + "ss >> {0};\n".format(param_name)
				content += "\t"*(tmp_len+1) + "ss.clear();\n"
				value = param_name
			content += "\t"*(tmp_len+1) + "{0}set{1}({2});\n".format(tmp, CStringTools.upperFirstByte(param_name), value)
			content += "\t"*tmp_len + "}\n"
			i += 1
		if isarr is True:
			# content += "\t"*1 + "}\n"
			content += "\t"*1 + "p->push_back(tmp);\n"
		content += "\n"
		content += "\t"*1 + "return ret;\n"
		content += "}\n"
		return content

	def __write_execute2(self, func_name, method_info):
		content = ""
		in_isarr = method_info.get(CSqlParse.IN_ISARR)
		if in_isarr is None:
			raise SystemExit("[Keyword Error] (function {0}) in_isarr is exist".format(func_name))
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		buf_len = method_info.get(CSqlParse.BUFLEN)
		if buf_len is None:
			buf_len = "512"
		is_brace = method_info.get(CSqlParse.IS_BRACE)
		if is_brace is None:
			is_brace = False
		is_group = method_info.get(CSqlParse.IS_GROUP)
		sql = method_info.get(CSqlParse.SQL)
		if sql is None:
			sql = ""
		sql = re.sub(r"\n", "\n\t\t", sql)
		n = 1
		if in_isarr == "true":
			n = 2
		if input_params is not None:
			content += "\t"*1 + 'std::string sql("");\n'
			if in_isarr == "true":
				content += "\t"*1 + "for (auto iter = input.begin(); iter != input.end(); ++iter)\n"
				content += "\t"*1 + "{\n"
			content += "\t"*n + "char buf[{0}];\n".format(buf_len)
			content += "\t"*n + "memset(buf, 0, sizeof(buf));\n"
			if is_group is None or is_group is False:
				if is_brace is False:
					content += "\t"*n + 'snprintf(buf, sizeof(buf), "{0}"\n'.format(self.__replace_sql_by_input_params(input_params, sql, False))
					content += "\t"*(n+1) + ", "
					content += self.__get_input_posture(in_isarr, input_params)
					content += ");\n"
				else:
					sql, fulls = self.__replace_sql_brace(input_params, sql, False)
					content += "\t"*n + 'snprintf(buf, sizeof(buf), "{0}"\n'.format(sql)
					content += "\t"*(n+1) + ", "
					content += self.__get_input_brace_posture(in_isarr, input_params, fulls)
					content += ");\n"
			else:
				content += self.__write_group(func_name, method_info, in_isarr, is_brace, input_params, sql, n)
			if in_isarr == "true":
				content += "\t"*n + "sql += buf;\n"
			else:
				content += "\t"*n + "sql = buf;\n"
		else:
			content += "\t"*1 + 'std::string sql = "{0}";\n'.format(sql)
		if in_isarr == "true":
			content += "\t"*1 + "}\n"
		content += "\t"*1 + 'm_mutex.lock();\n'
		if output_params is None:
			content += "\t"*1 + 'ret = sqlite3_exec(m_db, sql.c_str(), nullptr, nullptr, nullptr);\n'
		else:
			callback_name = func_name + "Callback"
			content += "\t"*1 + 'ret = sqlite3_exec(m_db, sql.c_str(), {0}, &output, nullptr);\n'.format(callback_name)
		content += "\t"*1 + 'm_mutex.unlock();\n'
		if in_isarr == "true":
			content += "\t"*1 + "if (ret != SQLITE_OK) return ret;\n"
		return content

	def __write_execute(self, func_name, method_info):
		content = ""
		in_isarr = method_info.get(CSqlParse.IN_ISARR)
		if in_isarr is None:
			raise SystemExit("[Keyword Error] (function {0}) in_isarr is exist".format(func_name))
		input_params = method_info.get(CSqlParse.INPUT_PARAMS)
		output_params = method_info.get(CSqlParse.OUTPUT_PARAMS)
		buf_len = method_info.get(CSqlParse.BUFLEN)
		if buf_len is None:
			buf_len = "512"
		is_brace = method_info.get(CSqlParse.IS_BRACE)
		if is_brace is None:
			is_brace = False
		is_group = method_info.get(CSqlParse.IS_GROUP)
		sql = method_info.get(CSqlParse.SQL)
		if sql is None:
			sql = ""
		sql = re.sub(r"\n", "\n\t\t", sql)
		n = 1
		if in_isarr == "true":
			n = 2
		content += "\t"*1 + 'm_mutex.lock();\n'
		if input_params is not None:
			content += "\t"*1 + 'sqlite3_exec(m_db, "begin transaction;", nullptr, nullptr, nullptr);\n'
			content += "\t"*1 + 'std::string sql("");\n'
			if in_isarr == "true":
				content += "\t"*1 + "for (auto iter = input.begin(); iter != input.end(); ++iter)\n"
				content += "\t"*1 + "{\n"
			content += "\t"*n + "char buf[{0}];\n".format(buf_len)
			content += "\t"*n + "memset(buf, 0, sizeof(buf));\n"
			if is_group is None or is_group is False:
				if is_brace is False:
					content += "\t"*n + 'snprintf(buf, sizeof(buf), "{0}"\n'.format(self.__replace_sql_by_input_params(input_params, sql, False))
					content += "\t"*(n+1) + ", "
					content += self.__get_input_posture(in_isarr, input_params)
					content += ");\n"
				else:
					sql, fulls = self.__replace_sql_brace(input_params, sql, False)
					content += "\t"*n + 'snprintf(buf, sizeof(buf), "{0}"\n'.format(sql)
					content += "\t"*(n+1) + ", "
					content += self.__get_input_brace_posture(in_isarr, input_params, fulls)
					content += ");\n"
			else:
				content += self.__write_group(func_name, method_info, in_isarr, is_brace, input_params, sql, n)
			content += "\t"*n + 'sql = buf;\n'
		else:
			content += "\t"*1 + 'std::string sql = "{0}";\n'.format(sql)
		if output_params is None:
			content += "\t"*n + 'ret = sqlite3_exec(m_db, sql.c_str(), nullptr, nullptr, nullptr);\n'
		else:
			callback_name = func_name + "Callback"
			content += "\t"*n + 'ret = sqlite3_exec(m_db, sql.c_str(), {0}, &output, nullptr);\n'.format(callback_name)
		if in_isarr == "true":
			content += "\t"*1 + "}\n"
		if input_params is not None:
			content += "\t"*1 + 'sqlite3_exec(m_db, "commit;", nullptr, nullptr, nullptr);\n'
		content += "\t"*1 + 'm_mutex.unlock();\n'
		if in_isarr == "true":
			content += "\t"*1 + "if (ret != SQLITE_OK) return ret;\n"
		return content

	def __write_group(self, func_name, method_info, in_isarr, is_brace, input_params, sql, n):
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
				this_field = "input."
				if in_isarr == "true":
					this_field = "iter->"
				content += "{0}get{1}Used() == {2}".format(this_field, CStringTools.upperFirstByte(group_input_params[i - 1].get(CSqlParse.PARAM_NAME)), t_f)
				if i < group_len:
					content += " && "
			if 1 not in group:
				sql_tmp = re.sub("where", "", sql_tmp)

			tmp = ""
			if is_brace is True:
				sql_tmp, fulls = self.__replace_sql_brace(input_params, sql_tmp, True)
				tmp += "\t"*(n+1) + 'snprintf(buf, sizeof(buf), "{0}"'.format(sql_tmp)
				if len(fulls) > 0:
					tmp += "\n" + "\t"*(n+2) + ", "
				tmp += self.__get_input_brace_posture(in_isarr, input_params, fulls)
				tmp += ");"
			else:
				tmp += "\t"*(n+1) + 'snprintf(buf, sizeof(buf), "{0}"'.format(self.__replace_sql_by_input_params(input_params, sql_tmp, True))
				if len(fulls) > 0:
					tmp += "\n" + "\t"*(n+2) + ", "
				tmp += self.__get_input_posture(in_isarr, input_params)
				tmp += ");"

			content += ") {\n" + "{0}\n".format(tmp) + "\t"*n + "}"
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

	def __get_input_posture(self, in_isarr, input_params):
		content = ""
		length = len(input_params)
		i = 0
		preix = "input."
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
		for number, keyword in fulls:
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

	def __replace_sql_brace(self, input_params, sql, is_group):
		fulls, max_number = CStringTools.get_brace_format_list(sql)
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
		for number, keyword in list(full_set):
			inpams = input_params[number]
			tmp = ""
			param_type = inpams.get(CSqlParse.PARAM_TYPE)
			if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
				tmp += '\\"'
			tmp += self.type2symbol(param_type)
			if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
				tmp += '\\"'
			sql = re.sub(keyword, tmp, sql)
		return sql, fulls

	def __replace_sql_by_input_params(self, input_params, sql, is_group):
		content = ""
		param_len = len(input_params)
		symbol_len = len(re.findall(r"\?", sql))
		if is_group is False:
			if param_len != symbol_len:
				str_tmp = "[Param Length Error] may be last #define error ? symbol length({1}) != params length({2})\n[sql] : \t{0}".format(sql, symbol_len, param_len)
				raise SystemExit(str_tmp)
		i = 0
		for ch in sql:
			if ch == "?":
				inpams = input_params[i]
				param_type = inpams.get(CSqlParse.PARAM_TYPE)
				symbol = self.type2symbol(param_type)
				if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
					content += '\\"'
				content += symbol
				if inpams.get(CSqlParse.PARAM_IS_CONDITION) is False:
					content += '\\"'
				i += 1
			else:
				content += ch
		# find {0} {1} ...
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
