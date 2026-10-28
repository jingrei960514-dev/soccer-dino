# 從 solution.ipynb（教師版）產生 game.ipynb（學生拿到的破壞版）。
# 修改教材時只改 solution.ipynb，再執行 python teacher/make_game_notebook.py，兩份就不會不一致。
# 做法：在 solution.ipynb 裡找出含有特定文字的格子，把整格換成下面寫好的破壞版內容，
# 其他格子（說明、球員設定、開始遊戲）原封不動。
# 教師版裡有答案的格子都要列在 replacements 裡，否則答案會原封不動帶到破壞版。

import json
import os


# 教師版和這個腳本一起放在 teacher 資料夾，產生的破壞版放在上一層，和學生的其他檔案在一起。
# 路徑從這個腳本的位置算，所以不管在哪個資料夾執行都找得到。
teacher_folder = os.path.dirname(os.path.abspath(__file__))
source_path = os.path.join(teacher_folder, 'solution.ipynb')
output_path = os.path.join(teacher_folder, '..', 'game.ipynb')


# ===== 破壞版的內容 =====
# 每一格都要能正常執行、不報錯，只是遊戲會「怪怪的」。
# 問題的編號依照格子由上到下的順序，學生從上往下修就不會跳來跳去。
# 遊戲規則的函式用「挖空」的方式：要填的地方寫成 ______（六個底線）。
# ______ 在 Python 裡是合法的變數名稱，所以這一格執行時不會出錯；
# 引擎看到函式裡還有 ______，就當作這個函式還沒寫，遊戲照常進行，只是會「壞掉」。
# 填空時要填的是「一段程式」，所以空格只能放在算式或名稱的位置，
# 例如 game.lives ______ 這種寫法填之前就是語法錯誤，整格都不能執行。

title_cell = '''
# 足球小恐龍

這個遊戲**壞掉了**！先玩玩看，找出哪裡怪怪的，再一項一項把它修好。

程式裡標了 **【問題一】** 到 **【問題四】**，從上到下依序修好它們。
看到 `______` 就是要填的空格，把整個 `______` 換成正確的程式。

## 怎麼玩

1. 從上到下，每一格按 `Shift + Enter` 執行。
2. 執行最後一格，遊戲視窗就會跳出來。如果沒看到，看一下工作列，它可能躲在瀏覽器後面。
3. 按空白鍵跳躍，閃過障礙物，抵達球門就過關！
4. 改完程式之後，要先**重新執行改過的那一格**，再執行最後一格，改動才會生效。
5. 函式裡只要還有一個 `______` 沒填，遊戲就會當作那個函式還沒寫好。
'''

course_cell = '''
# ===== 我的關卡 =====
# 【問題一】關卡裡全部都是三角錐，好無聊！
# 提示：把清單裡的一些 'cone' 換成其他名稱，可以用的名稱寫在上面的表格。
course = ['cone', 'cone', 'cone', 'cone', 'cone']
for i in range(3):
	course.append('cone')
	course.append('cone')
'''

jump_cell = '''
# ===== 遊戲規則 =====
jump_power = 12

# 按下跳躍鍵時會執行這裡
def on_jump_key(game):
	# 【問題二】按跳躍鍵，球員卻跳不起來！
	# 第一個空格：球員站在地上才能跳。「是否站在地上」是 game 的哪一個屬性？看上面的表格。
	# 第二個空格：往上跳，game.vy 要是負數（看上面的表格）。
	# 跳多高用這一格最上面自己定義的變數 jump_power（它不是 game 的，前面不用加 game.）。
	# 直接寫 jump_power 這個名字，前面要加什麼它才會變成負數？
	if game.______:
		game.vy = ______
'''

hit_cell = '''
# 撞到障礙時會執行這裡
def on_hit(game):
	# 【問題三】撞到障礙物，卻一點事都沒有！
	# 第一個空格：撞到時命要少一條，寫出「原本的命減一」。
	# 第二個空格：命剩下幾條的時候，遊戲要結束？
	# 第三個空格：讓遊戲結束的函式叫什麼？看上面的表格。
	game.lives = ______
	if game.lives == ______:
		game.______()
'''

tick_cell = '''
# 每過一秒會執行這裡
def on_tick(game):
	# 【問題四】畫面一直都是同一個速度，不夠刺激！
	# 空格：每過一秒讓速度變快一點，寫出「原本的速度加 0.2」。
	game.speed = ______
'''

# 教師版在 teacher 資料夾裡，要先把上一層加進搜尋路徑才找得到引擎；
# 學生的 notebook 和 soccer 資料夾放在一起，只要一行，所以整格換掉
import_cell = '''
# 載入遊戲引擎（這一格不用改）
from soccer import engine
'''

# 挑戰題換成半挖空的格子，教師版裡的完整答案才不會跟著帶到破壞版。
# 射門只挖空條件和射門的函式；「射完彈藥減一」故意不寫出來，讓學生自己想到要補上這一行。
# 挑戰一（二段跳）改的是 on_jump_key，已經被上面的 jump_cell 換掉了，不用另外處理
shoot_cell = '''
# ===== 挑戰二：射門 =====
# 在這裡寫 on_shoot_key(game)，寫好之後重新執行這一格
def on_shoot_key(game):
	# 第一個空格：有彈藥才能射門，寫出「彈藥大於 0」。
	# 第二個空格：射出一顆球的函式叫什麼？看上面的說明。
	if ______:
		game.______()
'''

# 每一組是一個清單：第一個是要找的文字，第二個是換成的內容。
# 要找的文字必須只出現在那一格裡，否則會換錯格子。
replacements = [
	['教師版', title_cell],
	['from soccer import engine', import_cell],
	['# ===== 我的關卡 =====', course_cell],
	['def on_jump_key', jump_cell],
	['def on_hit', hit_cell],
	['def on_tick', tick_cell],
	['# ===== 挑戰二：射門 =====', shoot_cell],
]


# notebook 裡每一格的 source 是「一行一個字串」的清單，每行結尾保留換行符號。
# strip 去掉頭尾多餘的空行，splitlines(True) 的 True 代表保留每行結尾的換行。
def text_to_source(text):
	return text.strip('\n').splitlines(True)


def source_to_text(source):
	text = ''
	for line in source:
		text = text + line
	return text


def main():
	with open(source_path, encoding='utf-8') as notebook_file:
		notebook = json.load(notebook_file)

	for pair in replacements:
		marker = pair[0]
		new_text = pair[1]
		found = False
		for cell in notebook['cells']:
			if marker in source_to_text(cell['source']):
				cell['source'] = text_to_source(new_text)
				found = True
				break
		# 找不到就停下來不寫檔，免得產生一份「少修改一項」的破壞版卻沒人發現
		if not found:
			print('找不到含有「' + marker + '」的格子，請檢查 solution.ipynb 是否被改過。')
			print('game.ipynb 沒有更新。')
			return

	# 清除所有執行結果，學生拿到的是乾淨的版本
	for cell in notebook['cells']:
		if cell['cell_type'] == 'code':
			cell['outputs'] = []
			cell['execution_count'] = None

	# ensure_ascii=False 讓中文直接存成中文，而不是 一 這種編碼，用文字編輯器打開也看得懂
	with open(output_path, 'w', encoding='utf-8', newline='\n') as notebook_file:
		json.dump(notebook, notebook_file, ensure_ascii=False, indent=1)
		notebook_file.write('\n')
	print('已產生 game.ipynb')


main()
