# 所有可以調整的數值都集中在這個檔案。
# 想改遊戲手感（重力、速度、障礙物大小、顏色）時只要改這裡，
# 不需要去讀 engine.py 或 drawing.py。
# 長度單位都是「像素」，時間單位都是「幀」（1 秒 = fps 幀）。

import os

import pygame


# ===== 視窗 =====
# 960 x 480 在一般筆電螢幕上不會超出畫面
screen_width = 960
screen_height = 480
# 每秒畫幾張畫面；所有速度都是「每一幀移動幾像素」，所以改這個會讓整個遊戲變快或變慢
fps = 60
window_title = '足球小恐龍'

# ===== 場地 =====
# 地面的高度（從視窗上緣往下數）；球員和地上的障礙物都踩在這條線上
ground_y = 400
# 天空的下緣，也就是看台的上緣
sky_bottom = 110
# 看台的下緣，也就是草地的上緣
stands_bottom = 210
# 草皮條紋的寬度
stripe_width = 160
# 草皮條紋要不要跟著畫面捲動。
# 整片草地一起滑動，眼睛會以為自己在動，很多人會頭暈，所以預設是 False（不動），
# 速度感改由腳下的一排小草來表現。想要更強的速度感可以改成 True 試試看
grass_scrolls = False
# 腳下小草的間距；這排小草一定會跟著捲動
grass_tuft_spacing = 90
# 觀眾圓點的間距與排數
crowd_spacing = 26
crowd_rows = 4

# ===== 球員 =====
# 球員固定在畫面的這個橫向位置，真正在移動的是背景和障礙物
player_x = 160
player_width = 40
player_height = 80

# ===== 物理 =====
# 每一幀往下增加的速度；數字愈大，跳起來落得愈快
gravity = 0.6
# 往上速度的上限；學生把 jump_power 設成 9999 時靠這個擋住，球員才不會飛出畫面太久
max_up_speed = 30
# 往下速度的上限
max_fall_speed = 30

# ===== 前進速度 =====
start_speed = 6
# 速度太快畫面會一次跳過障礙物，太慢（或負數）就永遠到不了球門，所以要設上下限
min_speed = 1
max_speed = 30

# ===== 生命 =====
start_lives = 3
# 被撞之後的無敵時間；90 幀 = 1.5 秒，避免同一個障礙物連續扣好幾條命
invincible_frames = 90

# ===== 關卡排列 =====
# 第一個關卡元素在世界中的位置；設成畫面寬度，開場時它剛好在畫面右邊外面
first_item_x = 960
# course 清單裡每一個元素佔用的寬度；調大會讓障礙物之間更鬆
slot_width = 340
# 最後一個元素之後還要跑多遠才到球門
goal_distance_after_course = 300
# course 清單裡可以用的名稱
course_item_names = ['cone', 'defender', 'high_ball', 'ball', 'gap']
# course 最多幾個元素；學生的迴圈寫錯時可能產生幾百萬個，遊戲會卡住，所以開始前先擋下來
max_course_length = 1000
# 名字和背號太長會超出畫面或球衣
max_name_length = 12
max_number_length = 3
# course 裡打錯的名稱最多列出幾個；全部列出來會洗掉整個畫面，學生反而找不到重點
max_course_problems_shown = 5

# ===== 關卡元素的大小 =====
cone_width = 36
cone_height = 44
defender_width = 72
defender_height = 34
ball_radius = 12
high_ball_radius = 13
# 高空球的底部和站著的球員頭頂之間的空隙；站著剛好不會碰到，一跳就會撞到
high_ball_gap = 6
# 高空球中心的高度，由上面的數值算出來，改上面的數字就好
high_ball_center_y = ground_y - player_height - high_ball_gap - high_ball_radius
# 防守球員鏟過來、高空球飛過來時，比畫面捲動再快多少
defender_extra_speed = 1.5
high_ball_extra_speed = 3
# 碰撞框往內縮的距離；縮一點會比較寬鬆，畫面上看起來擦到邊不會算撞到
hitbox_margin = 5
# 已經離開畫面左邊多遠的東西可以刪掉，免得清單愈來愈長
remove_behind_distance = 200

# ===== 射門 =====
# 射出去的球比畫面捲動再快多少
shot_speed = 12
shot_radius = 9
# 畫面上同時最多幾顆球；學生忘了扣彈藥又一直按時，靠這個避免球太多讓遊戲變慢
max_shots_on_screen = 3
# 被踢飛的防守球員每一幀往前、往上飛多少
kicked_fly_forward = 6
kicked_fly_up = 9

# ===== 分數 =====
# 每跑多少像素得 1 分
pixels_per_point = 10
# 撿到一顆地上的足球得幾分
ball_points = 50
# 射門踢飛一個防守球員得幾分
kick_points = 30

# ===== 官方模式 =====
# 亂數種子：同一個種子永遠產生同樣的關卡。比賽當天大家都用這個值，分數才能互相比較；
# 想換一套新關卡時改這個數字，但比賽進行中絕對不要改
official_seed = 20261005
official_jump_power = 12
# 每過一秒加多少速度，以及速度加到多少就不再加
official_speed_step = 0.15
official_max_speed = 16
# 跑到第幾格時難度達到最高
official_full_difficulty_slots = 60
# 一開始每一格有 50% 是空白，最難時降到 15%
official_gap_chance_start = 0.5
official_gap_chance_end = 0.15
# 不是空白時，各種元素出現的比例；加起來要等於 1
official_item_weights = [['cone', 0.35], ['defender', 0.25], ['high_ball', 0.2], ['ball', 0.2]]
# 跳過障礙物之後，至少要隔幾格才可以出現高空球，否則球員還在空中就會被打到
official_high_ball_safe_slots = 2
# 速度變快之後，跳一次在空中會跑得比較遠；格子如果不跟著變寬，連續兩個障礙物就會躲不掉。
# 所以每多一格，格子就加寬一點，加到第 official_slot_growth_until 格為止（340 + 100 x 5 = 840）。
# 用「第幾格」而不是「目前速度」來算，保證每個人的關卡位置完全一樣
official_slot_growth = 5
official_slot_growth_until = 100

# ===== 學生沒寫時的預設值 =====
default_player_name = '球員'
default_jersey_color = 'red'
default_jersey_number = 10
default_course = ['cone', 'gap', 'cone', 'gap', 'ball', 'gap', 'cone']

# ===== 按鍵 =====
jump_keys = [pygame.K_SPACE, pygame.K_UP, pygame.K_w]
shoot_keys = [pygame.K_f, pygame.K_x]
# 重新開始多放一個 Enter，萬一 R 被輸入法攔下來還有備案
restart_keys = [pygame.K_r, pygame.K_RETURN]
quit_key = pygame.K_ESCAPE

# ===== 圖片 =====
# 圖檔放在專案裡的 assets 資料夾。每個角色對應一個檔名，找不到檔案就用幾何圖形畫，所以一張都不放也能玩。
# 圖片會自動縮放成下面的大小；寬高最好照這個比例畫，才不會被拉扁。
# 背景圖不會捲動：整片背景一起滑動很容易頭暈
assets_folder = 'assets'
# assets 資料夾的完整路徑，由上面的名稱算出來。
# 以這個檔案所在的資料夾為準，而不是「目前的資料夾」，從別的地方執行 notebook 也找得到
assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), assets_folder)
image_files = {
	'player': 'player.png',
	'cone': 'cone.png',
	'defender': 'defender.png',
	'ball': 'ball.png',
	'high_ball': 'high_ball.png',
	'shot': 'shot.png',
	'goal': 'goal.png',
	'background': 'background.png',
}
# 障礙物的圖片大小直接用上面碰撞框的數值，改了障礙物大小，圖片也會跟著變，兩邊不會對不起來。
# 球員的圖比碰撞框寬一些（60 比 40），留空間給手臂，碰撞框窄一點玩起來也比較公平
image_sizes = {
	'player': (60, player_height),
	'cone': (cone_width, cone_height),
	'defender': (defender_width, defender_height),
	'ball': (ball_radius * 2, ball_radius * 2),
	'high_ball': (high_ball_radius * 2, high_ball_radius * 2),
	'shot': (shot_radius * 2, shot_radius * 2),
	'goal': (80, 150),
	'background': (screen_width, screen_height),
}

# ===== 音效 =====
# 音效檔也放在 assets 資料夾。想用 .ogg 檔的話，把下面的檔名改成 .ogg 就好。
# 找不到檔案時，用程式產生一個簡單的「嗶」聲代替，所以一個檔案都不放也有聲音
sound_enabled = True
# 音量，0 是靜音，1 是最大聲
sound_volume = 0.3
sound_files = {
	'jump': 'jump.wav',
	'hit': 'hit.wav',
	'ball': 'ball.wav',
	'shoot': 'shoot.wav',
	'kick': 'kick.wav',
	'win': 'win.wav',
	'lose': 'lose.wav',
}
# 找不到音效檔時的代替音：每一個音是 [頻率, 長度（毫秒）]，依序播放。
# 頻率愈高聲音愈尖，例如 440 是 Do Re Mi 的 La
beep_notes = {
	'jump': [[520, 60], [780, 60]],
	'hit': [[200, 90], [140, 140]],
	'ball': [[880, 50], [1320, 90]],
	'shoot': [[660, 40], [440, 60]],
	'kick': [[300, 50], [900, 80]],
	'win': [[523, 120], [659, 120], [784, 120], [1047, 260]],
	'lose': [[392, 160], [330, 160], [262, 320]],
}

# ===== 字型 =====
# 依序嘗試這些字型，找到第一個電腦上有的就用；pygame 內建字型沒有中文字，中文會變成方框
font_names = 'microsoftjhenghei,microsoftjhengheiui,msjh,pingfangtc,heititc,notosanscjktc,notosanstc,wenquanyizenhei,arialunicodems'

# ===== 球衣顏色 =====
# 學生在 notebook 裡寫的顏色名稱，對應到螢幕上的 RGB 顏色
jersey_colors = {
	'red': (220, 40, 40),
	'blue': (40, 90, 220),
	'green': (30, 140, 60),
	'yellow': (250, 210, 30),
	'white': (245, 245, 245),
	'black': (30, 30, 30),
	'orange': (250, 130, 20),
	'purple': (140, 60, 190),
	'pink': (250, 120, 180),
	'sky': (110, 190, 250),
	'gray': (130, 130, 130),
}

# ===== 其他顏色 =====
white = (255, 255, 255)
black = (0, 0, 0)
sky_color = (135, 200, 245)
stands_color = (70, 70, 90)
# 觀眾和草皮的顏色都刻意選低對比，背景太花俏會搶走障礙物的注意力，也容易頭暈
crowd_colors = [(120, 105, 115), (130, 125, 105), (105, 115, 135), (125, 125, 130), (110, 125, 110), (135, 115, 100)]
grass_light = (75, 165, 75)
grass_dark = (68, 155, 68)
line_color = (240, 240, 240)
grass_tuft_color = (45, 120, 45)
skin_color = (240, 200, 160)
shorts_color = (30, 30, 30)
shoe_color = (20, 20, 20)
cone_color = (255, 130, 0)
cone_base_color = (200, 90, 0)
defender_jersey_color = (100, 100, 120)
dust_color = (210, 200, 175)
net_color = (225, 225, 225)
heart_color = (230, 40, 60)
text_color = (255, 255, 255)
text_shadow_color = (0, 0, 0)
win_color = (255, 220, 0)
lose_color = (255, 90, 90)
official_badge_color = (250, 200, 30)
official_badge_text_color = (40, 30, 0)
progress_back_color = (30, 90, 30)
progress_fill_color = (200, 240, 120)
