# 足球小恐龍的遊戲引擎。
# 學生不會打開這個檔案。他們只在 notebook 裡寫變數和函式，再呼叫 engine.run(globals())，
# 由這裡讀出那些變數，並在適當的時機呼叫學生寫的函式（按跳躍鍵、撞到障礙、每過一秒）。
# 官方比賽則呼叫 engine.run_official(globals())，只用學生的球員設定，規則全部內建。
# 畫圖的部分全部放在 drawing.py，防呆的檢查與中文錯誤訊息放在 checks.py，這個檔案只管「遊戲規則與狀態」。

import os
import random
import sys

# 必須在 import pygame 之前設定，才能關掉 pygame 每次啟動時印出的歡迎訊息，免得學生以為出錯
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# 現場電腦的 Python 不一定裝了 pygame。直接 import 失敗的話，學生只會看到一長串英文錯誤，
# 所以先試試看，失敗就記下來，等到要開始遊戲時再顯示中文說明
try:
	import pygame
	pygame_ready = True
except ImportError:
	pygame_ready = False

# config.py、drawing.py、sound.py、checks.py 都會用到 pygame，所以確定有 pygame 才載入它們
if pygame_ready:
	import config
	import drawing
	import sound
	import checks


# 學生函式裡收到的 game 就是這個類別的物件。
# 把所有遊戲狀態放在同一個物件裡，學生只要記得「game.某某」就能讀寫。
class Game:
	# mode 是 'student'（學生模式）或 'official'（官方模式）
	def __init__(self, mode):
		# ===== 學生會用到的屬性 =====
		# 球員是否站在地上；跳躍前要先檢查，否則在空中一直按會一直往上飛
		self.on_ground = True
		# 垂直速度；負數往上、正數往下，因為螢幕的 y 座標是往下增加的
		self.vy = 0
		self.lives = config.start_lives
		# 畫面每一幀往左捲動幾像素
		self.speed = config.start_speed
		# 已經跳了幾次（二段跳用）；落地時引擎會自動歸零
		self.jump_count = 0
		# 射門用的彈藥，撿到地上的足球加一
		self.ammo = 0
		self.score = 0

		# ===== 引擎自己用的屬性 =====
		self.mode = mode
		# 球員腳底的 y 座標
		self.player_y = config.ground_y
		# 畫面已經往右捲了多遠；世界座標減掉它就是螢幕座標
		self.camera_x = 0
		# 關卡裡所有還沒被刪掉的元素，每個元素是一個字典
		self.things = []
		# 球門在世界中的位置（只有學生模式有球門）
		self.goal_x = 0
		self.balls_collected = 0
		self.defenders_kicked = 0
		# 射出去、還在畫面上的球，每顆是一個字典
		self.shots = []
		# 這一幀要播放的音效名稱。規則的部分只負責「放進來」，由主迴圈統一播放後清空，
		# 這樣 engine.py 的規則和聲音分開，沒有喇叭的電腦也不用改任何規則
		self.sounds_to_play = []
		# 大於 0 時代表正在無敵，每一幀減一
		self.invincible_timer = 0
		# 數到 fps 就代表過了一秒，要呼叫 on_tick
		self.tick_timer = 0
		# 總共畫了幾幀，畫跑步動畫時用
		self.frame_count = 0
		self.is_over = False
		# 'win' 代表抵達球門，'lose' 代表被 over() 結束
		self.result = ''
		# 0 到 1，代表離球門還有多遠，畫進度條用
		self.progress = 0

		# ===== 官方模式產生無盡關卡用 =====
		# 每一局都重新建立一個用固定種子的亂數產生器，所以每一局、每個人的關卡都一模一樣。
		# 用獨立的 random.Random 而不是直接用 random 模組，學生程式裡怎麼用亂數都不會影響它
		self.course_random = random.Random(config.official_seed)
		# 下一格要放在世界中的哪個位置，以及它是第幾格
		self.next_slot_x = config.first_item_x
		self.slot_index = 0
		# 距離上一個「要跳的障礙物」已經隔了幾格；用來避免高空球緊跟在跳躍之後
		self.slots_since_jump_obstacle = 99

		# 記下 game 原本有哪些屬性。學生把名稱打錯（例如 game.live）時，Python 會多出一個新屬性，
		# checks.py 拿這份清單比對就能發現。先放一個空清單，清單自己的名字才會被記進去
		self.known_attributes = []
		self.known_attributes = list(vars(self))

	# 學生在 on_hit 裡呼叫 game.over() 讓遊戲結束。
	# 這裡只做記號，真正停止更新、畫結束畫面由主迴圈處理；
	# 這樣學生函式執行到一半時，遊戲狀態不會突然被清空。
	def over(self):
		if self.is_over:
			return
		self.is_over = True
		self.result = 'lose'
		self.sounds_to_play.append('lose')

	# 學生在 on_shoot_key 裡呼叫 game.shoot() 射出一顆球。
	# 這裡刻意不檢查彈藥：「有彈藥才能射、射完減一」是學生要自己寫的規則。
	# 但畫面上同時存在的球有上限，免得學生忘了扣彈藥又一直按，球太多讓遊戲變慢。
	def shoot(self):
		if len(self.shots) >= config.max_shots_on_screen:
			return
		shot = {}
		# 從球員腳前出發；用世界座標記錄，和關卡元素的算法一樣
		shot['x'] = self.camera_x + config.player_x + 20
		self.shots.append(shot)
		self.sounds_to_play.append('shoot')


# ===== 對外的兩個函式 =====

# 學生模式：game.ipynb、solution.ipynb 的最後一格呼叫這個函式。
# student_globals 是學生那邊的 globals()，也就是一個字典，裡面有學生定義的所有變數和函式。
def run(student_globals):
	if not can_start(student_globals):
		return

	# 開始前先檢查學生的設定，有問題就不開視窗，直接列出所有問題
	problems = checks.check_student_settings(student_globals)
	if len(problems) > 0:
		print_problems('【遊戲沒有開始】請先修正下面的問題：', problems)
		return

	# 還有空格沒填的函式、名字很像但不完全一樣的函式，都只提醒，遊戲照常開始
	warnings = checks.find_blank_functions(student_globals)
	warnings = warnings + checks.find_misspelled_functions(student_globals)
	if len(warnings) > 0:
		print_problems('【提醒】遊戲照常開始，但請檢查：', warnings)

	settings = read_student_settings(student_globals)
	start_game(settings)


# 官方模式：official.ipynb 的最後一格呼叫這個函式。
# 只讀學生的球員設定，關卡和規則都由引擎決定，這樣大家的分數才能互相比較。
def run_official(student_globals):
	if not can_start(student_globals):
		return

	problems = checks.check_player_settings(student_globals)
	if len(problems) > 0:
		print_problems('【遊戲沒有開始】請先修正下面的問題：', problems)
		return

	settings = read_official_settings(student_globals)
	start_game(settings)


# 兩種模式開始前都要確認的兩件事：電腦有沒有 pygame、最後一格有沒有寫對。
# 有問題就印出中文說明並回傳 False。這裡用 print 而不是丟出錯誤，學生才不會看到 traceback。
def can_start(student_globals):
	if not pygame_ready:
		print('這台電腦的 Python 沒有安裝 pygame，遊戲沒辦法開始。請舉手找助教。')
		print()
		print('給助教：這個 notebook 目前使用的 Python 是')
		print('\t' + sys.executable)
		print('請在 Jupyter 右上角把 kernel 換成已經安裝 pygame 的 Python，或在終端機執行：')
		print('\t"' + sys.executable + '" -m pip install pygame')
		return False
	# 學生可能把最後一格改成 engine.run() 或 engine.run(course)
	if not isinstance(student_globals, dict):
		print('最後一格要寫成 engine.run(globals())，括號裡的 globals() 不能改。')
		return False
	return True


# 把問題清單印成一個框，每個問題前面加一個點。
def print_problems(title, problems):
	lines = []
	for problem in problems:
		lines.append('・' + problem)
	print(checks.make_message_box(title, lines))


# 兩種模式共用的部分：開視窗、一局接一局地玩、最後關視窗。
def start_game(settings):
	# 學生的函式出錯時，要等視窗關掉之後才印出說明，所以先記在這裡
	message = ''
	# 混音器的設定必須在 pygame.init() 之前
	sound.prepare_mixer()
	pygame.init()
	# 用 try / finally 包起來：不管遊戲是正常結束還是中途出錯，都一定會執行 pygame.quit()，
	# 視窗才會真的關掉。在 Jupyter 裡如果沒關，下次執行會卡住或開不了新視窗。
	# 注意這裡不能用 sys.exit()，那會把 Jupyter 的 kernel 一起關掉。
	try:
		screen = pygame.display.set_mode((config.screen_width, config.screen_height))
		pygame.display.set_caption(config.window_title)
		# pygame 2 預設會開啟「文字輸入」，切到中文輸入法時字母鍵會被輸入法拿去組字，
		# 遊戲就收不到 R、W 這些按鍵。這個遊戲不需要打字，所以把它關掉。
		# 舊版 pygame 沒有這個函式，用 hasattr 先檢查，才不會報錯
		if hasattr(pygame.key, 'stop_text_input'):
			pygame.key.stop_text_input()
		clock = pygame.time.Clock()
		fonts = drawing.load_fonts()
		# 圖片和音效每次開始都重新載入：pygame.quit() 之後舊的就不能用了，
		# 而且這樣換了 assets 裡的檔案，不用重新啟動 kernel 也會生效
		images = drawing.load_images()
		sounds = sound.load_sounds()

		keep_playing = True
		while keep_playing:
			keep_playing = play_one_round(screen, clock, fonts, images, sounds, settings)
	except checks.StudentCodeError as error:
		# 學生的函式出錯：中文說明已經寫在錯誤裡了，取出來，等視窗關掉再印
		message = str(error)
	except KeyboardInterrupt:
		# 在 Jupyter 按了「中斷」（方塊按鈕）。這不是錯誤，不需要顯示一長串 traceback
		message = '遊戲被中斷了。要再玩一次，重新執行最後一格就好。'
	finally:
		pygame.quit()

	if message != '':
		print(message)


# ===== 讀取學生的設定 =====

# 兩種模式都會用到的球員設定：名字、球衣顏色、背號。
# 學生沒有定義的項目就用 config.py 裡的預設值，所以不會報錯。
def read_player_settings(student_globals):
	settings = {}
	settings['player_name'] = str(student_globals.get('player_name', config.default_player_name))
	settings['jersey_color'] = student_globals.get('jersey_color', config.default_jersey_color)
	settings['jersey_number'] = str(student_globals.get('jersey_number', config.default_jersey_number))

	# 顏色名稱轉成 RGB；開始前 checks.py 已經確認過顏色名稱是對的，所以可以直接查
	settings['jersey_rgb'] = config.jersey_colors[settings['jersey_color']]
	return settings


# 學生模式：球員設定之外，再讀關卡和學生寫的函式。
# 沒有定義的函式記成 None，代表「什麼都不做」，所以學生刪掉某個函式也不會報錯。
def read_student_settings(student_globals):
	settings = read_player_settings(student_globals)
	settings['mode'] = 'student'
	# 複製一份清單，遊戲過程中不會改到學生原本的 course
	settings['course'] = list(student_globals.get('course', config.default_course))

	for function_name in checks.function_descriptions:
		student_function = student_globals.get(function_name)
		# 還有 ______ 沒填的函式當作還沒寫。
		# 否則一呼叫就會出錯、遊戲停下來，學生就沒辦法先試玩壞掉的版本，找出哪裡怪怪的
		if student_function is not None and checks.has_blank(student_function):
			student_function = None
		settings[function_name] = student_function
	return settings


# 官方模式：只讀球員設定，規則換成引擎內建的函式。
# 內建函式和學生函式放在同一個位置，所以主迴圈完全不用分辨現在是哪一種模式。
def read_official_settings(student_globals):
	settings = read_player_settings(student_globals)
	settings['mode'] = 'official'
	settings['course'] = []
	settings['on_jump_key'] = official_on_jump_key
	settings['on_hit'] = official_on_hit
	settings['on_tick'] = official_on_tick
	settings['on_shoot_key'] = official_on_shoot_key
	return settings


# 呼叫學生寫的某個函式。所有對學生函式的呼叫都經過這裡，所以防呆只需要寫在這一個地方。
def call_student_function(settings, function_name, game):
	student_function = settings[function_name]
	if student_function is None:
		return
	# 學生的函式出錯時，換成一個帶有中文說明的 StudentCodeError 丟出去，
	# start_game() 接到之後會先關掉視窗，再印出說明。
	# Exception 不包含 KeyboardInterrupt，所以在 Jupyter 按中斷不會被當成學生寫錯
	try:
		student_function(game)
	except Exception as error:
		raise checks.StudentCodeError(checks.explain_error(function_name, student_function, error))
	# 函式本身沒出錯，但可能把 game 的數值改壞了（例如變成文字），也要檢查
	checks.check_game_values(game, function_name)


# ===== 官方模式的內建規則 =====
# 寫法刻意和 solution.ipynb 及延伸功能的參考答案一樣，學生看到也看得懂。

# 二段跳：jump_count 記錄已經跳了幾次，落地時引擎會自動歸零
def official_on_jump_key(game):
	if game.jump_count < 2:
		game.vy = -config.official_jump_power
		game.jump_count = game.jump_count + 1


# 射門：有彈藥才能射，射完彈藥減一
def official_on_shoot_key(game):
	if game.ammo > 0:
		game.shoot()
		game.ammo = game.ammo - 1


def official_on_hit(game):
	game.lives = game.lives - 1
	if game.lives <= 0:
		game.over()


def official_on_tick(game):
	if game.speed < config.official_max_speed:
		game.speed = game.speed + config.official_speed_step


# ===== 一局遊戲 =====

# 玩一局。回傳 True 代表玩家按了重新開始，回傳 False 代表要關閉視窗。
def play_one_round(screen, clock, fonts, images, sounds, settings):
	game = Game(settings['mode'])
	if game.mode == 'student':
		build_course(game, settings['course'])

	# 主迴圈：每跑一圈就是一幀
	while True:
		# 1. 處理鍵盤和關閉視窗
		action = handle_events(game, settings)
		if action == 'quit':
			return False
		if action == 'restart':
			return True

		# 2. 更新遊戲狀態；遊戲結束後就停住，只畫結束畫面
		if not game.is_over:
			update_game(game, settings)

		# 3. 播放這一幀發生的音效（跳躍、撞到、撿球……），播完就清空
		sound.play_sounds(sounds, game.sounds_to_play)
		game.sounds_to_play = []

		# 4. 把這一幀畫出來
		drawing.draw_frame(screen, fonts, images, game, settings)
		pygame.display.flip()

		# 5. 等待，讓遊戲固定每秒跑 fps 幀，不會因為電腦快慢而不同
		clock.tick(config.fps)


# 學生模式：把學生的 course 清單一次全部變成放在世界中的元素。
# 每個名稱佔一格 slot_width 的寬度，'gap' 只佔位置、不放東西。
def build_course(game, course):
	x = config.first_item_x
	for name in course:
		if name != 'gap':
			game.things.append(make_thing(name, x))
		x = x + config.slot_width
	game.goal_x = x + config.goal_distance_after_course


# 官方模式：關卡沒有盡頭，所以不能一次全部產生。
# 每一幀檢查一下，畫面右邊外面快沒東西了，就再往後多產生幾格。
def extend_official_course(game):
	while game.next_slot_x < game.camera_x + config.screen_width + config.slot_width:
		name = pick_official_item(game)
		if name != 'gap':
			game.things.append(make_thing(name, game.next_slot_x))
		game.next_slot_x = game.next_slot_x + get_official_slot_width(game.slot_index)
		game.slot_index = game.slot_index + 1


# 官方關卡第 slot_index 格的寬度：愈後面愈寬，才跟得上愈來愈快的速度。
def get_official_slot_width(slot_index):
	growing_slots = slot_index
	if growing_slots > config.official_slot_growth_until:
		growing_slots = config.official_slot_growth_until
	return config.slot_width + growing_slots * config.official_slot_growth


# 決定官方關卡的下一格要放什麼。
# 每一格只抽一次 random()，而且結果只跟「第幾格」有關、跟時間或玩家表現無關，
# 所以只要種子一樣，每個人遇到的關卡就完全一樣。
# 不用 random.choice() 是因為不同 Python 版本的 choice 算法可能不同，random() 則保證相同。
def pick_official_item(game):
	roll = game.course_random.random()

	# 難度從 0 慢慢增加到 1：愈後面，空白愈少
	difficulty = game.slot_index / config.official_full_difficulty_slots
	if difficulty > 1:
		difficulty = 1
	gap_chance = config.official_gap_chance_start + (config.official_gap_chance_end - config.official_gap_chance_start) * difficulty

	if roll < gap_chance:
		name = 'gap'
	else:
		# 把剩下的機率依照比例分給各種元素。
		# 例如權重是 cone 0.35、defender 0.25，那 roll 落在 0 到 0.35 就是 cone，0.35 到 0.6 就是 defender
		roll = (roll - gap_chance) / (1 - gap_chance)
		name = config.official_item_weights[-1][0]
		total = 0
		for pair in config.official_item_weights:
			total = total + pair[1]
			if roll < total:
				name = pair[0]
				break

	# 公平性：剛跳過障礙物時球員還在空中，緊接著的高空球一定躲不掉，所以改成空白
	if name == 'high_ball' and game.slots_since_jump_obstacle < config.official_high_ball_safe_slots:
		name = 'gap'

	if name == 'cone' or name == 'defender':
		game.slots_since_jump_obstacle = 0
	else:
		game.slots_since_jump_obstacle = game.slots_since_jump_obstacle + 1
	return name


# 一個關卡元素就是一個字典。
# 'kind' 是種類，'x' 是它在世界中的左邊界，'done' 代表已經撞過或撿過，不再觸發。
def make_thing(kind, x):
	thing = {}
	thing['kind'] = kind
	thing['x'] = x
	thing['done'] = False
	# 'kicked' 代表防守球員被射門踢飛了，'lift' 是他飛離地面多高，畫飛走的動畫用
	thing['kicked'] = False
	thing['lift'] = 0
	return thing


# ===== 事件處理 =====

# 讀取這一幀的所有鍵盤與視窗事件。
# 回傳 'quit'（關閉）、'restart'（重新開始）或空字串（繼續玩）。
def handle_events(game, settings):
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			return 'quit'
		if event.type != pygame.KEYDOWN:
			continue
		if event.key == config.quit_key:
			return 'quit'
		if event.key in config.restart_keys:
			return 'restart'
		# 遊戲結束後按跳躍鍵不應該再呼叫學生的函式
		if game.is_over:
			continue
		if event.key in config.jump_keys:
			# 跳躍的規則是學生寫的，引擎不知道他有沒有真的讓球員跳起來，
			# 所以比較呼叫前後的 vy：變得更往上（更小）才播放跳躍聲
			vy_before = game.vy
			call_student_function(settings, 'on_jump_key', game)
			if game.vy < vy_before:
				game.sounds_to_play.append('jump')
		elif event.key in config.shoot_keys:
			call_student_function(settings, 'on_shoot_key', game)
	return ''


# ===== 每一幀的更新 =====

# 每一幀依序做這些事；順序很重要，例如要先移動再檢查碰撞。
def update_game(game, settings):
	game.frame_count = game.frame_count + 1

	# 1. 每過一秒呼叫一次 on_tick
	game.tick_timer = game.tick_timer + 1
	if game.tick_timer >= config.fps:
		game.tick_timer = 0
		call_student_function(settings, 'on_tick', game)

	# 2. 學生可能把數值設得很極端，先拉回合理範圍，遊戲才不會壞掉
	game.speed = keep_in_range(game.speed, config.min_speed, config.max_speed)
	game.vy = keep_in_range(game.vy, -config.max_up_speed, config.max_fall_speed)

	# 3. 球員受重力影響上下移動
	update_player(game)

	# 4. 畫面往右捲動，官方模式在前方補上新的關卡，會自己動的障礙物再多移動一點
	game.camera_x = game.camera_x + game.speed
	if game.mode == 'official':
		extend_official_course(game)
	move_things(game)

	# 5. 射出去的球往前飛，碰到防守球員就把他踢飛
	move_shots(game)

	# 6. 檢查球員有沒有撞到障礙物或撿到球
	check_collisions(game, settings)

	# 7. 無敵時間倒數
	if game.invincible_timer > 0:
		game.invincible_timer = game.invincible_timer - 1

	# 8. 分數 = 跑的距離 + 撿到的球 + 踢飛的防守球員
	distance_points = int(game.camera_x / config.pixels_per_point)
	ball_points = game.balls_collected * config.ball_points
	kick_points = game.defenders_kicked * config.kick_points
	game.score = distance_points + ball_points + kick_points

	# 9. 學生模式才有球門：計算進度，並檢查是否抵達球門
	if game.mode == 'student':
		total_distance = game.goal_x - config.player_x
		game.progress = keep_in_range(game.camera_x / total_distance, 0, 1)
		if not game.is_over and game.camera_x + config.player_x >= game.goal_x:
			game.is_over = True
			game.result = 'win'
			game.sounds_to_play.append('win')


# 跳躍物理：每一幀速度加上重力，位置加上速度。
# 學生只要在 on_jump_key 裡把 vy 設成負數，球員就會自己往上再落下。
def update_player(game):
	game.vy = game.vy + config.gravity
	game.player_y = game.player_y + game.vy

	if game.player_y >= config.ground_y:
		# 落地：停在地面上，並把跳躍次數歸零，二段跳才能重新使用
		game.player_y = config.ground_y
		game.vy = 0
		game.on_ground = True
		game.jump_count = 0
	else:
		game.on_ground = False

	# 撞到視窗上緣就停住，避免跳躍力太大時球員消失在畫面外很久
	if game.player_y < config.player_height:
		game.player_y = config.player_height
		game.vy = 0


# 防守球員和高空球會主動往球員衝過來，所以除了跟著畫面捲動，還要再多往左移。
# 同時把已經遠遠落在畫面左邊外的東西刪掉，官方模式的清單才不會無限變長。
def move_things(game):
	remaining_things = []
	for thing in game.things:
		screen_x = thing['x'] - game.camera_x
		if thing['kicked']:
			# 被踢飛的防守球員往右上方飛走
			thing['x'] = thing['x'] + game.speed + config.kicked_fly_forward
			thing['lift'] = thing['lift'] + config.kicked_fly_up
		elif screen_x < config.screen_width:
			# 只有進入畫面後才開始移動，否則還沒出現就跑到別的障礙物身上去了
			if thing['kind'] == 'defender':
				thing['x'] = thing['x'] - config.defender_extra_speed
			elif thing['kind'] == 'high_ball':
				thing['x'] = thing['x'] - config.high_ball_extra_speed

		# 已經掉到畫面左邊外、或飛出畫面上方的就刪掉
		if screen_x > -config.remove_behind_distance and thing['lift'] < config.screen_height:
			remaining_things.append(thing)
	game.things = remaining_things


# 射出去的球每一幀往前飛，碰到還沒被踢飛的防守球員就把他踢飛，球也跟著消失。
# 球只對防守球員有效，碰到三角錐、地上的球、高空球都直接穿過去，規則比較單純。
def move_shots(game):
	remaining_shots = []
	for shot in game.shots:
		shot['x'] = shot['x'] + game.speed + config.shot_speed
		shot_rect = get_shot_rect(shot, game.camera_x)

		hit_defender = False
		for thing in game.things:
			if thing['kind'] != 'defender' or thing['done']:
				continue
			if shot_rect.colliderect(get_thing_rect(thing, game.camera_x)):
				thing['done'] = True
				thing['kicked'] = True
				game.defenders_kicked = game.defenders_kicked + 1
				hit_defender = True
				game.sounds_to_play.append('kick')
				break

		# 沒有踢到人、也還沒飛出畫面右邊的球才留下來
		if not hit_defender and shot['x'] - game.camera_x < config.screen_width + 50:
			remaining_shots.append(shot)
	game.shots = remaining_shots


# 檢查球員和每個關卡元素有沒有重疊。
def check_collisions(game, settings):
	player_rect = get_player_rect(game)
	for thing in game.things:
		if thing['done']:
			continue
		thing_rect = get_thing_rect(thing, game.camera_x)
		# 不認識的種類沒有碰撞框，直接跳過
		if thing_rect is None:
			continue
		if not player_rect.colliderect(thing_rect):
			continue

		if thing['kind'] == 'ball':
			# 撿到足球：加分、加一發彈藥
			thing['done'] = True
			game.balls_collected = game.balls_collected + 1
			game.ammo = game.ammo + 1
			game.sounds_to_play.append('ball')
		elif game.invincible_timer == 0:
			# 撞到障礙物。先設定無敵再呼叫學生的 on_hit，
			# 這樣就算學生在 on_hit 裡做了什麼，同一幀也不會被下一個障礙物再撞一次
			thing['done'] = True
			game.invincible_timer = config.invincible_frames
			game.sounds_to_play.append('hit')
			call_student_function(settings, 'on_hit', game)


# 球員的碰撞框，比畫出來的樣子小一圈，讓玩家覺得判定比較公平。
def get_player_rect(game):
	margin = config.hitbox_margin
	left = config.player_x - config.player_width // 2 + margin
	top = int(game.player_y) - config.player_height + margin
	width = config.player_width - margin * 2
	height = config.player_height - margin
	return pygame.Rect(left, top, width, height)


# 關卡元素的碰撞框（螢幕座標）。不認識的種類回傳 None。
def get_thing_rect(thing, camera_x):
	kind = thing['kind']
	left = int(thing['x'] - camera_x)
	margin = config.hitbox_margin

	if kind == 'cone':
		width = config.cone_width
		height = config.cone_height
		top = config.ground_y - height
	elif kind == 'defender':
		width = config.defender_width
		height = config.defender_height
		top = config.ground_y - height
	elif kind == 'ball':
		width = config.ball_radius * 2
		height = width
		top = config.ground_y - height
	elif kind == 'high_ball':
		width = config.high_ball_radius * 2
		height = width
		top = config.high_ball_center_y - config.high_ball_radius
	else:
		return None

	return pygame.Rect(left + margin, top + margin, width - margin * 2, height - margin)


# 射出去的球的碰撞框（螢幕座標）。球一律貼著地面滾，所以在空中射門也踢得到防守球員。
def get_shot_rect(shot, camera_x):
	size = config.shot_radius * 2
	left = int(shot['x'] - camera_x)
	return pygame.Rect(left, config.ground_y - size, size, size)


# 把數值限制在 low 到 high 之間。
def keep_in_range(value, low, high):
	if value < low:
		return low
	if value > high:
		return high
	return value
