# 清除 notebook 的執行結果，交給學生之前執行一次。
# 在專案資料夾的終端機輸入：
#	python clear_outputs.py                 清除這個資料夾裡所有的 .ipynb
#	python clear_outputs.py game.ipynb      只清除指定的 notebook
# 為什麼要清除：執行結果會存進 .ipynb 檔裡，學生打開就會看到上一個人的錯誤訊息或分數，
# 而且每次執行過檔案內容都會改變，用 git 比較版本時會多出一堆不重要的差異。

import json
import os
import sys


# 清除一個 notebook，回傳 True 代表有東西被清掉、檔案已經改寫。
def clear_notebook(path):
	with open(path, encoding='utf-8') as notebook_file:
		original_text = notebook_file.read()
	notebook = json.loads(original_text)

	for cell in notebook['cells']:
		# 說明文字的格子沒有執行結果
		if cell['cell_type'] != 'code':
			continue
		cell['outputs'] = []
		# 格子左邊的 [3] 這種執行順序編號
		cell['execution_count'] = None
		# VS Code 和 JupyterLab 會在格子的 metadata 記下執行時間，也一起清掉
		if 'metadata' in cell and 'execution' in cell['metadata']:
			del cell['metadata']['execution']

	# 存檔格式和 make_game_notebook.py 一樣：中文直接存成中文、縮排 1 格、結尾換行
	new_text = json.dumps(notebook, ensure_ascii=False, indent=1) + '\n'
	if new_text == original_text:
		return False
	with open(path, 'w', encoding='utf-8', newline='\n') as notebook_file:
		notebook_file.write(new_text)
	return True


def main():
	if len(sys.argv) > 1:
		paths = sys.argv[1:]
	else:
		# 沒有指定檔案時，找出這個腳本所在資料夾裡所有的 .ipynb
		folder = os.path.dirname(os.path.abspath(__file__))
		paths = []
		for file_name in sorted(os.listdir(folder)):
			if file_name.endswith('.ipynb'):
				paths.append(os.path.join(folder, file_name))

	for path in paths:
		if clear_notebook(path):
			print('已清除：' + os.path.basename(path))
		else:
			print('本來就是乾淨的：' + os.path.basename(path))


main()
