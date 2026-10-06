# 防呆：遊戲開始前檢查學生的設定；遊戲中學生的函式出錯時，翻譯成簡短的中文說明。
# 使用者是剛學 Python 的國中生，一長串英文 traceback 對他們沒有幫助，
# 所以這裡的每一則訊息都盡量回答三件事：哪裡錯了、可能的原因、要怎麼改。
# engine.py 只決定「什麼時候檢查」，訊息怎麼寫全部集中在這個檔案，之後要改用語只改這裡。

import difflib
import traceback

import config


# 學生的函式在遊戲中出錯時，引擎會丟出這種錯誤。
# 自己定義一種錯誤，是為了和其他錯誤分開：引擎只接住這一種，關掉視窗後印出中文訊息；
# 其他錯誤（引擎自己的 bug）照常顯示 traceback，開發時才看得到問題在哪裡。
class StudentCodeError(Exception):
	pass


# 引擎會呼叫的學生函式，以及各自在什麼時候執行；出錯時用來告訴學生是哪一個
function_descriptions = {
	'on_jump_key': '按下跳躍鍵時執行',
	'on_hit': '撞到障礙時執行',
	'on_tick': '每過一秒執行',
	'on_shoot_key': '按下射門鍵時執行',
}

# game 裡學生會改到、而且必須是數字的屬性；不是數字的話，引擎計算時就會出錯
number_attributes = ['vy', 'lives', 'speed', 'jump_count', 'ammo']

# 學生可以用的 game 屬性與函式；學生打錯字時，從這裡找出最像的名字提示他
student_attribute_names = ['on_ground', 'vy', 'lives', 'speed', 'jump_count', 'ammo', 'over', 'shoot']
# 同一份清單列給學生看的寫法；函式後面加上括號，提醒學生要用「呼叫」的
student_attribute_display = ['game.on_ground', 'game.vy', 'game.lives', 'game.speed', 'game.jump_count', 'game.ammo', 'game.over()', 'game.shoot()']


# ===== 訊息的格式 =====

# 把訊息包在兩條分隔線中間，在 notebook 一長串輸出裡比較顯眼。
def make_message_box(title, lines):
	text = '=' * 50 + '\n'
	text = text + title + '\n'
	for line in lines:
		text = text + line + '\n'
	text = text + '=' * 50
	return text


# 在 choices 裡找出和 text 最像的一個，找到就回傳「是不是要寫……？」，找不到回傳空字串。
# difflib 是 Python 內建的模組，get_close_matches 會比較兩段文字有多像；
# 最後的 0.6 是門檻，愈接近 1 要愈像才算數。
def suggest(text, choices):
	matches = difflib.get_close_matches(text.strip().lower(), choices, 1, 0.6)
	if len(matches) == 0:
		return ''
	return '是不是要寫 ' + repr(matches[0]) + '？'


# 文字或整數都可以當作名字和背號。
# bool 在 Python 裡也算整數（True 等於 1），但寫 True 一定是寫錯了，所以要排除。
def is_text_or_whole_number(value):
	if isinstance(value, bool):
		return False
	return isinstance(value, str) or isinstance(value, int)


# ===== 遊戲開始前的檢查 =====
# 每個檢查都回傳一個「問題清單」，清單是空的代表沒問題。
# 一次把所有問題都找出來，學生才不用改一個、執行一次，才看到下一個。

# 學生模式：球員、關卡、函式都要檢查。
def check_student_settings(student_globals):
	problems = check_player_settings(student_globals)
	problems = problems + check_course(student_globals)
	problems = problems + check_functions(student_globals)
	return problems


# 兩種模式都要檢查的球員設定。學生沒寫的項目會用預設值，所以只檢查有寫的。
def check_player_settings(student_globals):
	problems = []

	if 'player_name' in student_globals:
		name = student_globals['player_name']
		if not is_text_or_whole_number(name):
			problems.append('player_name 要是文字，前後加上引號，例如 player_name = \'小明\'。你寫的是 ' + repr(name) + '。')
		elif str(name).strip() == '':
			problems.append('player_name 是空的，請在引號裡寫上你的名字。')
		elif len(str(name)) > config.max_name_length:
			problems.append('player_name 太長了，最多 ' + str(config.max_name_length) + ' 個字。')

	if 'jersey_color' in student_globals:
		color = student_globals['jersey_color']
		color_names = list(config.jersey_colors)
		if not isinstance(color, str):
			problems.append('jersey_color 要是文字，前後加上引號，例如 jersey_color = \'red\'。你寫的是 ' + repr(color) + '。')
		elif color not in config.jersey_colors:
			problems.append('jersey_color 沒有 ' + repr(color) + ' 這個顏色。' + suggest(color, color_names))
			problems.append('可以用的顏色：' + '、'.join(color_names))

	if 'jersey_number' in student_globals:
		number = student_globals['jersey_number']
		if not is_text_or_whole_number(number):
			problems.append('jersey_number 要是整數，例如 jersey_number = 10。你寫的是 ' + repr(number) + '。')
		elif str(number).strip() == '':
			problems.append('jersey_number 是空的，請寫一個號碼，例如 jersey_number = 10。')
		elif len(str(number)) > config.max_number_length:
			problems.append('jersey_number 太長了，最多 ' + str(config.max_number_length) + ' 位數。')

	return problems


# 檢查 course 清單：型別、長度，以及每一個名稱是不是引擎認得的。
def check_course(student_globals):
	if 'course' not in student_globals:
		return []
	course = student_globals['course']

	if not isinstance(course, list) and not isinstance(course, tuple):
		return ['course 要是清單，用中括號把名稱包起來，例如 course = [\'cone\', \'gap\']。你寫的是 ' + repr(course) + '。']
	if len(course) == 0:
		return ['course 是空的清單，至少要放一個名稱。']
	if len(course) > config.max_course_length:
		return ['course 太長了，有 ' + str(len(course)) + ' 個，最多 ' + str(config.max_course_length) + ' 個。檢查迴圈的 range 是不是寫太大了。']

	problems = []
	wrong_count = 0
	for index in range(len(course)):
		name = course[index]
		if name in config.course_item_names:
			continue
		wrong_count = wrong_count + 1
		# 太多錯誤只列出前面幾個，後面用一句話帶過
		if wrong_count > config.max_course_problems_shown:
			continue
		# 同時寫出「第幾個」和清單的索引，學生數清單或看程式都對得起來
		position = 'course 的第 ' + str(index + 1) + ' 個（course[' + str(index) + ']）'
		if isinstance(name, str):
			problems.append(position + '是 ' + repr(name) + '，引擎不認得這個名稱。' + suggest(name, config.course_item_names))
		else:
			problems.append(position + '是 ' + repr(name) + '，名稱要用引號包起來，例如 \'cone\'。')

	if wrong_count > config.max_course_problems_shown:
		problems.append('course 裡還有 ' + str(wrong_count - config.max_course_problems_shown) + ' 個名稱也有問題，先修好上面幾個再執行一次。')
	if wrong_count > 0:
		problems.append('course 可以用的名稱：' + '、'.join(config.course_item_names))
	return problems


# 檢查學生定義的函式：必須真的是函式，而且括號裡剛好有一個 game。
# 沒定義的函式不用檢查，引擎會當作「什麼都不做」。
def check_functions(student_globals):
	problems = []
	for function_name in function_descriptions:
		if function_name not in student_globals:
			continue
		student_function = student_globals[function_name]
		if not callable(student_function):
			problems.append(function_name + ' 應該是函式，要寫成 def ' + function_name + '(game):。你寫的是 ' + repr(student_function) + '。')
			continue
		# 用 def 寫的函式才有 __code__，裡面的 co_argcount 是括號裡參數的數量。
		# 少寫 game 的話，引擎呼叫時才會出錯，所以開始前就先擋下來
		if hasattr(student_function, '__code__') and student_function.__code__.co_argcount != 1:
			problems.append(function_name + ' 的括號裡要剛好寫一個 game，也就是 def ' + function_name + '(game):。')
	return problems


# 找出名字很像、但不完全一樣的函式，例如 on_jump 或 on_jumpkey。
# 名字打錯時引擎不會呼叫它，遊戲看起來像「沒寫一樣」，學生很難自己發現。
# 這裡只提醒、不擋下遊戲：Jupyter 會記住改名之前的舊函式，擋下來的話，學生改好之後還是開不了遊戲。
def find_misspelled_functions(student_globals):
	warnings = []
	for name in student_globals:
		value = student_globals[name]
		# 只看用 def 寫的函式，而且名字不是引擎認得的
		if name in function_descriptions or not hasattr(value, '__code__'):
			continue
		matches = difflib.get_close_matches(name, list(function_descriptions), 1, 0.75)
		if len(matches) > 0:
			warnings.append('你定義了 ' + name + '，但引擎只認得 ' + matches[0] + '，名字要完全一樣才會被執行。')
	if len(warnings) > 0:
		warnings.append('如果已經改好名字了，可以忽略這個提醒；在 Jupyter 選「Restart Kernel」再執行一次，它就會消失。')
	return warnings


# ===== 遊戲中，學生的函式出錯 =====

# 把學生函式丟出的錯誤翻譯成中文說明，回傳整段要印出來的文字。
def explain_error(function_name, student_function, error):
	lines = []
	lines.append('出錯的函式：' + function_name + '（' + function_descriptions[function_name] + '）')
	line_text = find_error_line(student_function, error)
	if line_text != '':
		lines.append('出錯的那一行：' + line_text)
	lines.append('可能的原因：' + guess_reason(student_function, error))
	lines.append('改好之後，先重新執行改過的那一格，再執行最後一格。')
	lines.append('原始訊息（給助教看）：' + type(error).__name__ + ': ' + str(error))
	return make_message_box('【遊戲停止了】你寫的函式出錯了', lines)


# 從錯誤的追蹤紀錄裡，找出學生程式中出錯的那一行。
# 追蹤紀錄是一層一層的呼叫，最後幾層可能在 engine.py 裡（例如 game.shoot()），
# 所以只看和學生函式在同一個檔案（同一格）的那幾層，取最後一個。
def find_error_line(student_function, error):
	student_file = student_function.__code__.co_filename
	line_text = ''
	for frame in traceback.extract_tb(error.__traceback__):
		if frame.filename == student_file and frame.line:
			line_text = frame.line.strip()
	return line_text


# Python 的錯誤訊息會把出問題的名字放在單引號裡，例如 name 'jump_powr' is not defined。
# 用單引號切開之後，倒數第二段就是最後一個被引號包住的名字。
def get_last_quoted(message):
	parts = message.split('\'')
	if len(parts) < 3:
		return ''
	return parts[-2]


# 依照錯誤的種類猜可能的原因。只列出初學者最常遇到的幾種，其他的請助教看原始訊息。
# UnboundLocalError 是 NameError 的一種，所以要先檢查它；順序反過來就永遠輪不到它。
def guess_reason(student_function, error):
	message = str(error)
	name = get_last_quoted(message)

	if isinstance(error, UnboundLocalError):
		return '在函式裡改了 ' + name + '，Python 就把它當成函式自己的新變數，但它還沒有值。想讓數值一直累積，請改 game 的屬性，例如 game.speed。'

	if isinstance(error, NameError):
		# 學生自己的變數和函式都在 __globals__ 裡，從裡面找最像的名字；底線開頭的是 Jupyter 自己用的，不列入
		student_names = []
		for global_name in student_function.__globals__:
			if not global_name.startswith('_'):
				student_names.append(global_name)
		reason = '用到了 ' + name + '，但找不到這個名字。可能是打錯字，或是定義它的那一格還沒執行。'
		matches = difflib.get_close_matches(name, student_names, 1, 0.6)
		if len(matches) > 0:
			reason = reason + '是不是要寫 ' + matches[0] + '？'
		return reason

	if isinstance(error, AttributeError):
		if '\'Game\' object' in message:
			# 常見的情況：把自己定義的變數（例如 jump_power）寫成 game.jump_power
			if name in student_function.__globals__:
				return name + ' 是你自己定義的變數，不是 game 的屬性，前面不用加 game.，直接寫 ' + name + ' 就好。'
			reason = 'game 沒有 ' + name + ' 這個屬性。'
			matches = difflib.get_close_matches(name, student_attribute_names, 1, 0.75)
			if len(matches) > 0:
				reason = reason + '是不是要寫 game.' + matches[0] + '？'
			return reason + '可以用的有：' + '、'.join(student_attribute_display)
		return '點後面的名字 ' + name + ' 不存在，檢查有沒有打錯字。'

	if isinstance(error, TypeError):
		if 'not callable' in message:
			return '只有函式後面可以加括號 ( )，例如 game.over()；game.speed 這種數字後面不能加括號。'
		if 'argument' in message:
			return '呼叫函式時，括號裡的東西太多或太少。game.over() 和 game.shoot() 的括號裡不用放東西。'
		if '\'str\'' in message:
			return '文字和數字不能直接一起運算。檢查數字是不是被引號包起來了，例如 \'12\' 要寫成 12。'
		return '資料的型別不對，例如把文字和數字放在一起運算。'

	if isinstance(error, ZeroDivisionError):
		return '除以 0 了，數學上沒有答案。檢查除號 / 後面的數字會不會變成 0。'
	if isinstance(error, RecursionError):
		return '函式一直呼叫自己，停不下來。檢查函式裡是不是又呼叫了同一個函式。'
	if isinstance(error, IndexError):
		return '清單裡沒有這個位置。清單的位置從 0 開始數，最後一個是「長度減一」。'
	if isinstance(error, OverflowError):
		return '數字太大了，超過電腦能算的範圍。'
	return '程式執行時出錯了，請把這段訊息給助教看。'


# 學生的函式執行完之後，檢查它有沒有把 game 改壞。
# 這些錯誤當下不會發生，要等引擎拿數值來計算時才會出錯，那時訊息會指向 engine.py，學生看不懂，
# 所以在學生函式剛執行完就檢查，才能告訴他是哪一個函式造成的。
def check_game_values(game, function_name):
	function_line = '出錯的函式：' + function_name + '（' + function_descriptions[function_name] + '）'

	# 1. 必須是數字的屬性被改成文字或其他東西。
	# value != value 只有在 value 是 NaN（不是數字的特殊小數）時才會成立，例如 0 * 無限大
	for name in number_attributes:
		value = getattr(game, name)
		is_number = isinstance(value, int) or isinstance(value, float)
		if not is_number or value != value:
			lines = [function_line]
			lines.append('執行完之後，game.' + name + ' 變成了 ' + repr(value) + '，但它必須是數字。')
			lines.append('檢查數字是不是被引號包起來了，例如 \'12\' 要寫成 12。')
			raise StudentCodeError(make_message_box('【遊戲停止了】game.' + name + ' 不是數字', lines))

	# 2. 學生把屬性名稱打錯，例如 game.live = game.lives - 1。
	# Python 不會報錯，而是幫 game 多加一個叫 live 的屬性，結果命永遠不會變少，學生很難發現。
	# 學生自己加的、和內建名稱不像的屬性（例如 game.my_counter）不擋，留給學生發揮創意。
	# 所以門檻設得比較嚴（0.8）：game.vyy、game.live 會被抓到，game.my_counter 不會被當成 jump_count
	for name in vars(game):
		if name in game.known_attributes:
			continue
		if name == 'over' or name == 'shoot':
			lines = [function_line]
			lines.append('game.' + name + ' 是要「呼叫」的函式，要寫成 game.' + name + '()，不是 game.' + name + ' = ……。')
			raise StudentCodeError(make_message_box('【遊戲停止了】game.' + name + ' 的用法不對', lines))
		matches = difflib.get_close_matches(name, student_attribute_names, 1, 0.8)
		if len(matches) > 0:
			lines = [function_line]
			lines.append('函式裡寫了 game.' + name + '，但 game 沒有這個屬性，是不是要寫 game.' + matches[0] + '？')
			lines.append('名字打錯時遊戲不會報錯，但數值永遠不會改變，所以先幫你攔下來。')
			raise StudentCodeError(make_message_box('【遊戲停止了】game.' + name + ' 可能打錯字了', lines))
