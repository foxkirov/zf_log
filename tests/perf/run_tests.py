#!/usr/bin/python

import sys
import os
import argparse
import json

def readable_test(test):
	if "call_site_size" == test:
		return "1. Call site size"
	if "executable_size" == test:
		return "2. Executable size"
	if "compile_time" == test:
		return "3. Compile time"
	if "link_time" == test:
		return "4. Link time"
	return test

def readable_subj(subj):
	if "zf_log_n" == subj:
		return "zf_log"
	if "easylog" == subj:
		return "Easylogging++"
	return subj

class data_test:
	def __init__(self, value):
		if type(value) is not str:
			raise RuntimeError("Not a string")
		self.value = value
	def __str__(self):
		return readable_test(self.value)
	def __repr__(self):
		return repr(self.value)

class data_subj:
	def __init__(self, value):
		if type(value) is not str:
			raise RuntimeError("Not a string")
		self.value = value
	def __str__(self):
		return readable_subj(self.value)
	def __repr__(self):
		return repr(self.value)

class data_bytes:
	def __init__(self, value):
		if type(value) is not int:
			raise RuntimeError("Not an int")
		self.value = value
	def __str__(self):
		if self.value < 1024:
			return "%ib " % (self.value)
		if self.value < 1024 * 1024:
			return "%.2fkb" % (self.value / 1024.0)
		return "%.2fmb" % (self.value / 1024.0 / 1024.0)
	def __repr__(self):
		return repr(self.value)

class data_seconds:
	def __init__(self, value):
		if type(value) is not int and type(value) is not float:
			raise RuntimeError("Not an int or float")
		self.value = value
	def __str__(self):
		return "%.3fsec" % (self.value)
	def __repr__(self):
		return repr(self.value)

def to_table_str(value, w=0):
	if value is None:
		return "-".center(w)
	elif type(value) is int:
		return '{0:\'}'.format(value).rjust(w)
	elif type(value) is str:
		return value.center(w)
	elif isinstance(value, data_test):
		return str(value).ljust(w)
	elif isinstance(value, data_subj):
		return str(value).center(w)
	elif isinstance(value, data_bytes):
		return str(value).rjust(w)
	elif isinstance(value, data_seconds):
		return str(value).rjust(w)
	else:
		raise RuntimeError("Type not supported: " + str(type(value)))


def run_call_site_size(params):
	ps = params["call_site_size"]
	result = dict()
	for subj in ps:
		sz1 = os.path.getsize(ps[subj]["1"])
		sz2 = os.path.getsize(ps[subj]["2"])
		result[subj] = data_bytes(sz2 - sz1)
	return result

def run_min_executable_size(params):
	ps = params["executable_size"]
	result = dict()
	for subj in ps.keys():
		sz = os.path.getsize(ps[subj])
		result[subj] = data_bytes(sz)
	return result

def run_compile_time(params):
	ps = params["compile_time"]
	result = dict()
	for subj in ps.keys():
		with open(ps[subj], "r") as f:
			dt = json.load(f)["dt"]
			result[subj] = data_seconds(dt)
	return result

def run_link_time(params):
	ps = params["link_time"]
	result = dict()
	for subj in ps.keys():
		with open(ps[subj], "r") as f:
			dt = json.load(f)["dt"]
			result[subj] = data_seconds(dt)
	return result

def run_tests(params):
	result = dict()
	result["call_site_size"] = run_call_site_size(params)
	result["executable_size"] = run_min_executable_size(params)
	result["compile_time"] = run_compile_time(params)
	result["link_time"] = run_link_time(params)
	return result

def write_table(result, out):
	tests = sorted(result.keys(), key=readable_test)
	subjs = set()
	# collect all subjects
	for test in tests:
		subjs.update(result[test].keys())
	subjs = sorted(list(subjs), key=readable_subj)
	# create table
	rows = len(tests) + 1
	cols = len(subjs) + 1
	table = [[None for _ in range(cols)] for _ in range(rows)]
	# put names and captions
	for i in range(1, rows):
		table[i][0] = data_test(tests[i - 1])
	for j in range(1, cols):
		table[0][j] = data_subj(subjs[j - 1])
	# put data
	for i in range(1, rows):
		for j in range(1, cols):
			test = tests[i - 1]
			subj = subjs[j - 1]
			if subj in result[test]:
				table[i][j] = result[test][subj]
	# find cols width
	widths = [0 for _ in range(cols)]
	for j in range(0, cols):
		for i in range(0, rows):
			s = to_table_str(table[i][j])
			if widths[j] < len(s):
				widths[j] = len(s)
	# draw chart
	margins = 2
	line = "+" + "-" * (sum(widths) + margins * len(widths) + len(widths) - 1) + "+"
	chart = line + "\n"
	for i in range(0, rows):
		chart += "|"
		for j in range(0, cols):
			w = widths[j]
			s = to_table_str(table[i][j], w)
			chart += s.center(w + margins) + "|"
		chart += "\n" + line + "\n"
	out.write(chart)

def main(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--out", metavar="PATH",
			help="Output file path")
	parser.add_argument("-p", "--parameter", metavar="VALUE", action="append", default=[],
			help="Input parameter")
	parser.add_argument("-b", "--build", metavar="TYPE",
			help="Input parameter")
	args = parser.parse_args(argv[1:])
	# process parameters
	params = dict()
	for p in args.parameter:
		d = params
		vs = p.split(":")
		key = None
		for i in range(len(vs)):
			if i == len(vs) - 1:
				d[key] = vs[i]
				break
			if key is not None:
				d = d[key]
			key = vs[i]
			if key not in d:
				d[key] = dict()
	sys.stderr.write(json.dumps(params, indent=4, default=repr))
	# run tests
	result = run_tests(params)
	# print results
	out = sys.stdout
	if args.out is not None:
		out = open(args.out, 'w')
	out.write(json.dumps(params, indent=4, default=repr))
	out.write(json.dumps(result, indent=4, default=repr))
	out.write("\n")
	write_table(result, out)
	out.flush()
	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))