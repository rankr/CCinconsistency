'''
extract C-code comments from file
'''
import os
import re
import subprocess
import Queue

def valid_double_quotation_mark(string):
	'''
	WARNING: this function assume that you are in string state
	'''
	last = ''
	for i, j in enumerate(string):
		if j == '\\':
			if last != '\\':
				last = '\\'
			else:
				last = ''
		elif j == '"':
			if last != '\\':
				return i
			else:
				last = ''
		else:
			last = ''
	return -1

def valid_double_quotation_mark_nan(string):
	'''
	WARNING: this function assume that you are in nan state
	'''
	temp = string
	while True:
		string_posi = temp.find('"')
		#if " is in form as '"' or '\"', it is not valid!
		if (string_posi<len(temp)-1 and string_posi>0 \
			and temp[string_posi-1]=='\'' and temp[string_posi+1]=='\'') or \
			(string_posi<len(temp)-1 and string_posi>1 \
			and temp[string_posi-2]=='\'' and temp[string_posi-1]=='\\' and temp[string_posi+1]=='\''):
			temp = temp[string_posi+2]
		else:
			return string_posi

def valid_inline_comment(string):
	'''
	judge if a line of source code has inline comment
	return -1: not has inline comment
	'''
	while True:
		block_posi = string.find('/*')
		inline_posi = string.find('//')
		string_posi = valid_double_quotation_mark_nan(string)
		temp = []
		if block_posi > -1:
			temp.append(block_posi)
		if inline_posi > -1:
			temp.append(inline_posi)
		if string_posi > -1:
			temp.append(string_posi)
		if not temp:
			return -1
		mini = min(temp)
		if block_posi == mini:
			return -1
		if inline_posi == mini:
			return inline_posi
		else:#string posi is the minium
			next_quot = valid_double_quotation_mark(string[string_posi+1:])
			if next_quot == -1:
				return -1
			else:
				string = string[next_quot+1:]

def extract_comment(file_path, opened_file):
	if not os.path.exists(file_path) or os.path.isdir(file_path):
		print "Error: Illegal file path \"%s\"to function extract_comment"%(file_path)
		return
	'''
	state pool:
	'nan': no special pattern
	'in block comments': have detect valid '/*' in a line before and not see a valid '*/'' yet
	'in inline comments': have detect many continuous lines of inline comments
	'in string': have detect valid string-beginner '"' and not see another valid '"' yet
	
	what to extract and store in file:
	the path of file containing the comments
	the begin line number & end line number of a comment
	the type of comments (block or inline comments)
	the location of comments (head or not)
	content of comment
	'''
	#the column of store.csv: ['file_path','begin', 'end', 'cmt_type','if_head', 'length', 'content']
	w = opened_file
	f = open(file_path, 'r')

	state = 'nan'
	file_head = 1
	if_head = 1
	cmt = ''
	begin_num = -1
	end_num = -1
	line_num = 1
	i = f.readline()
	while True:
		if i == '':
			#print line_num, state
			i = f.readline()
			line_num += 1
			file_head = 0
			if not i:
				if state == 'in block comments' or state == 'in string':
					print 'there may be compiling error in %d line of file %s'%(line_num, file_path)
					return
				elif state == 'in inline comments':
					end_num = line_num - 1
					temp = "%s,%d,%d,%s,%d,%d,%s\n"%(file_path, begin_num, \
						end_num, 'inline', if_head, len(cmt), re.sub(',', '$@$', re.sub('\n', '$%$', cmt)))
					w.write(temp)
				break
		if state == 'nan':
			block_posi = i.find('/*')
			inline_posi = i.find('//')
			string_posi = valid_double_quotation_mark_nan(i)
			temp = []
			if block_posi > -1:
				temp.append(block_posi)
			if inline_posi > -1:
				temp.append(inline_posi)

			if string_posi > -1:
				temp.append(string_posi)
			if not temp:
				i = ''
				continue
			mini = min(temp)
			if block_posi == mini:
				state = 'in block comments'
				begin_num = line_num
				if_head = file_head
				i = i[block_posi+2:]
			elif inline_posi == mini:
				state = 'in inline comments'
				begin_num = line_num
				cmt = i[inline_posi+2:]
				if_head = file_head
				i = ''
			else:
				state = 'in string'
				i = i[string_posi+1:]
		elif state == 'in string':
			end_posi = valid_double_quotation_mark(i)
			if end_posi != -1:
				state = 'nan'
				i = i[end_posi+1:]
			else:
				i = ''
		elif state == 'in block comments':
			end_posi = i.find('*/')
			if end_posi != -1:
				state = 'nan'
				end_num = line_num
				cmt += i[:end_posi]
				temp = "%s,%d,%d,%s,%d,%d,%s\n"%(file_path, begin_num, \
					end_num, 'inline', if_head, len(cmt), re.sub(',', '$@$', re.sub('\n', '$%$', cmt)))
				w.write(temp)
				cmt = ''
				i = i[end_posi+2:]
			else:
				cmt += i
				i = ''
		elif state == 'in inline comments':
			inline_posi = valid_inline_comment(i)
			if inline_posi == -1:
				state = 'nan'
				end_num = line_num - 1
				temp = "%s,%d,%d,%s,%d,%d,%s\n"%(file_path, begin_num, \
					end_num, 'inline', if_head, len(cmt), re.sub(',', '$@$', re.sub('\n', '$%$', cmt)))
				w.write(temp)
				cmt = ''
			else:
				cmt += i[inline_posi+2:]
				i = ''

def extract_comment_from_repo(repo_path, store_path, appendix = []):
	'''
	filter to 
	'''
	if not filter:
		print 'Please specify some type of file to extract!'
		return
	if not os.path.isdir(repo_path):
		print 'Your input repo_path is illegal'
		return
	q = Queue.Queue()
	q.put(repo_path)

	w = open(store_path, 'a')
	w.write(','.join(['file_path','begin', 'end', 'cmt_type','if_head', 'length', 'content']) + '\n')
	while not q.empty():
		now_path = q.get()
		temp = os.listdir(now_path)
		for i in temp:
			p = os.path.join(now_path, i)
			if os.path.isdir(p):
				q.put(p)
			else:
				a = p.split('.')[-1]
				if a in appendix:
					extract_comment(p, w)
