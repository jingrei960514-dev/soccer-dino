# 開發用的入口：不用開 Jupyter，直接執行 notebook 裡的程式。
# 在專案資料夾的終端機輸入：
#	python run.py                執行 solution.ipynb（教師版）
#	python run.py game.ipynb     執行其他 notebook，例如破壞版
# notebook 是唯一的版本，這裡不再抄一份程式，才不會兩邊改了一邊、忘了另一邊。

import json
import linecache
import sys


# 讀出 notebook 裡所有程式格的內容，接成一整段程式碼。
# .ipynb 其實是 JSON 檔：cells 是一個清單，每一格的 source 是「一行一個字串」的清單。
def read_notebook_code(path):
	with open(path, encoding='utf-8') as notebook_file:
		notebook = json.load(notebook_file)

	code = ''
	for cell in notebook['cells']:
		# 說明文字的格子（markdown）不是程式，跳過
		if cell['cell_type'] != 'code':
			continue
		for line in cell['source']:
			code = code + line
		# 每一格最後一行通常沒有換行，補上一個，免得和下一格黏在一起
		code = code + '\n'
	return code


def main():
	if len(sys.argv) > 1:
		path = sys.argv[1]
	else:
		path = 'solution.ipynb'

	code = read_notebook_code(path)
	# 學生的函式出錯時，checks.py 會顯示「出錯的那一行」，Python 是用檔名去 linecache 查那一行的內容。
	# 這段程式碼不是真的檔案（直接打開 .ipynb 會讀到 JSON），所以用一個特別的名字，
	# 並把程式碼先放進 linecache，查的時候才拿得到正確的那一行。Jupyter 自己也是這樣做的
	code_name = '<' + path + '>'
	linecache.cache[code_name] = (len(code), None, code.splitlines(True), code_name)
	# 用一個空字典當作 notebook 的全域空間，notebook 裡的 globals() 拿到的就是這個字典。
	notebook_globals = {}
	exec(compile(code, code_name, 'exec'), notebook_globals)


main()
