# 所有「畫東西」的程式都放在這裡，engine.py 只管規則。
# 每一種角色都會先找 assets 資料夾裡的圖檔，找不到才用這裡的幾何圖形畫，所以一張圖都不放也能玩。
# 圖檔的名稱和大小寫在 config.py 的 image_files 和 image_sizes。

import math
import os

import pygame

import config


# ===== 字型與文字 =====

# 準備好幾種大小的字型，放在字典裡，畫文字時用 fonts['large'] 這樣取用。
# 字型只能在 pygame.init() 之後建立，所以由 engine.run() 呼叫。
def load_fonts():
	fonts = {}
	fonts['small'] = pygame.font.SysFont(config.font_names, 20)
	fonts['medium'] = pygame.font.SysFont(config.font_names, 30)
	fonts['large'] = pygame.font.SysFont(config.font_names, 48)
	fonts['huge'] = pygame.font.SysFont(config.font_names, 80)
	fonts['number'] = pygame.font.SysFont(config.font_names, 18, True)
	return fonts


# 畫一行有陰影的文字；陰影讓白字在草地或天空上都看得清楚。
# align 是 'left'、'right' 或 'center'，代表 (x, y) 是文字的左上角、右上角或上緣中間。
def draw_text(screen, font, text, color, x, y, align):
	shadow_image = font.render(text, True, config.text_shadow_color)
	text_image = font.render(text, True, color)
	rect = text_image.get_rect()
	if align == 'left':
		rect.topleft = (x, y)
	elif align == 'right':
		rect.topright = (x, y)
	else:
		rect.midtop = (x, y)
	screen.blit(shadow_image, (rect.x + 2, rect.y + 2))
	screen.blit(text_image, rect)
	# 回傳文字佔的範圍，需要在文字旁邊再畫東西時可以用
	return rect


# ===== 圖片 =====

# 載入 assets 裡的圖檔，回傳一個字典，例如 images['cone'] 就是三角錐的圖。
# 找不到的圖檔就不放進字典，畫的時候查不到，就改用幾何圖形。
# convert_alpha() 必須在開視窗之後才能用，所以由 engine.start_game() 開好視窗後呼叫。
def load_images():
	images = {}
	for name in config.image_files:
		file_name = config.image_files[name]
		path = os.path.join(config.assets_path, file_name)
		if not os.path.exists(path):
			continue
		try:
			# convert_alpha() 把圖轉成和螢幕一樣的格式，並保留透明的部分，之後每一幀畫起來比較快
			image = pygame.image.load(path).convert_alpha()
		except pygame.error:
			print('assets 裡的 ' + file_name + ' 讀不出來，改用幾何圖形。請確認它是 png 或 jpg 圖檔。')
			continue
		# 縮放成固定大小，不管原圖多大，碰撞判定都和畫面上看到的一樣
		images[name] = pygame.transform.smoothscale(image, config.image_sizes[name])
	return images


# 把圖片畫在「左下角是 (left, bottom)」的位置。
# 用底部對齊，因為遊戲裡的東西幾乎都是站在地面上，用底部算位置最直覺。
def draw_image(screen, image, left, bottom):
	rect = image.get_rect()
	rect.bottomleft = (int(left), int(bottom))
	screen.blit(image, rect)


# ===== 每一幀的總入口 =====

# 依照「由遠到近」的順序畫，後畫的會蓋住先畫的。
def draw_frame(screen, fonts, images, game, settings):
	draw_background(screen, images, game.camera_x)
	# 官方模式是無盡關卡，沒有球門
	if game.mode == 'student':
		draw_goal(screen, images, game.goal_x - game.camera_x)
	for thing in game.things:
		draw_thing(screen, images, thing, game.camera_x, game.frame_count)
	for shot in game.shots:
		draw_shot(screen, images, shot, game.camera_x, game.frame_count)
	draw_player(screen, fonts, images, game, settings)
	draw_hud(screen, fonts, game, settings)
	if game.is_over:
		draw_end_screen(screen, fonts, game, settings)


# ===== 背景 =====

# 背景：有 background.png 就直接貼上，沒有就畫天空、看台、草地。
# 不管哪一種，腳下的小草都會跟著捲動，讓玩家感覺到速度。
def draw_background(screen, images, camera_x):
	if 'background' in images:
		# 先塗滿天空色再貼圖：背景圖如果有透明的地方，沒塗的話上一幀的畫面會留下來，變成殘影
		screen.fill(config.sky_color)
		screen.blit(images['background'], (0, 0))
	else:
		draw_stadium(screen, camera_x)
	draw_grass_tufts(screen, camera_x)


# 用幾何圖形畫出天空、看台、草地和邊線。
def draw_stadium(screen, camera_x):
	# 天空
	screen.fill(config.sky_color)

	# 看台
	stands_height = config.stands_bottom - config.sky_bottom
	pygame.draw.rect(screen, config.stands_color, (0, config.sky_bottom, config.screen_width, stands_height))

	# 觀眾：一排排低彩度的圓點。
	# 看台刻意不捲動：它在很遠的地方，而且大片細碎的圖案一起移動很容易讓人頭暈。
	# 顏色由「第幾排第幾個」算出來，不用亂數，每一幀才會畫得一模一樣
	people_per_row = config.screen_width // config.crowd_spacing + 1
	for row in range(config.crowd_rows):
		y = config.sky_bottom + 16 + row * 22
		# 單數排往右錯開半格，看起來比較像真的座位
		stagger = (row % 2) * config.crowd_spacing // 2
		for column in range(people_per_row):
			x = column * config.crowd_spacing + stagger
			color_index = column * 7 + row * 3
			color = config.crowd_colors[color_index % len(config.crowd_colors)]
			pygame.draw.circle(screen, color, (x, y), 7)

	# 草地底色
	grass_height = config.screen_height - config.stands_bottom
	pygame.draw.rect(screen, config.grass_light, (0, config.stands_bottom, config.screen_width, grass_height))

	# 深色條紋，每隔一條畫一次。
	# 預設不跟著捲動：整片草地一起滑動會讓眼睛以為自己在動，很容易頭暈
	if config.grass_scrolls:
		stripe_offset = int(camera_x) % (config.stripe_width * 2)
	else:
		stripe_offset = 0
	x = -stripe_offset
	while x < config.screen_width:
		pygame.draw.rect(screen, config.grass_dark, (x, config.stands_bottom, config.stripe_width, grass_height))
		x = x + config.stripe_width * 2

	# 遠處和近處的邊線
	pygame.draw.line(screen, config.line_color, (0, config.stands_bottom + 6), (config.screen_width, config.stands_bottom + 6), 3)
	pygame.draw.line(screen, config.line_color, (0, config.ground_y + 30), (config.screen_width, config.ground_y + 30), 3)


# 腳下一排小草跟著捲動，讓玩家感覺到速度。
# 只有一條細細的範圍在動，比整片草地一起動舒服很多
def draw_grass_tufts(screen, camera_x):
	tuft_offset = int(camera_x) % config.grass_tuft_spacing
	x = -tuft_offset
	while x < config.screen_width:
		pygame.draw.line(screen, config.grass_tuft_color, (x, config.ground_y + 8), (x + 4, config.ground_y + 2), 2)
		pygame.draw.line(screen, config.grass_tuft_color, (x + 6, config.ground_y + 8), (x + 8, config.ground_y + 1), 2)
		pygame.draw.line(screen, config.grass_tuft_color, (x + 10, config.ground_y + 8), (x + 14, config.ground_y + 3), 2)
		x = x + config.grass_tuft_spacing


# ===== 足球 =====

# 畫一顆足球：白色圓形加上黑色花紋。angle 會隨時間改變，看起來像在滾動。
def draw_soccer_ball(screen, center_x, center_y, radius, angle):
	center_x = int(center_x)
	center_y = int(center_y)
	pygame.draw.circle(screen, config.white, (center_x, center_y), radius)
	pygame.draw.circle(screen, config.black, (center_x, center_y), max(2, radius // 3))
	# 外圍 5 個小黑點，平均分布在 360 度上
	for i in range(5):
		dot_angle = math.radians(angle + i * 72)
		dot_x = center_x + int(math.cos(dot_angle) * radius * 0.7)
		dot_y = center_y + int(math.sin(dot_angle) * radius * 0.7)
		pygame.draw.circle(screen, config.black, (dot_x, dot_y), max(1, radius // 5))
	# 外框
	pygame.draw.circle(screen, config.black, (center_x, center_y), radius, 1)


# ===== 球員 =====

def draw_player(screen, fonts, images, game, settings):
	# 無敵時閃爍：每 6 幀換一次「畫」或「不畫」
	if game.invincible_timer > 0 and (game.invincible_timer // 6) % 2 == 0:
		return

	x = config.player_x
	feet_y = int(game.player_y)

	# 跑步動畫：在地上時兩隻腳前後交換；在空中時固定成跨步的姿勢
	if game.on_ground:
		if (game.frame_count // 6) % 2 == 0:
			leg_swing = 7
		else:
			leg_swing = -7
	else:
		leg_swing = 9

	# 有 player.png 就用圖片，圖片的底部中間對準球員的腳。
	# 注意：用圖片時看不到學生選的球衣顏色和背號，因為那些畫在圖片裡了
	if 'player' in images:
		image_width = config.image_sizes['player'][0]
		draw_image(screen, images['player'], x - image_width // 2, feet_y)
	else:
		draw_player_body(screen, fonts, settings, x, feet_y, leg_swing)

	# 腳下帶著的球：在地上時跟著步伐前後動一點
	ball_x = x + 24 + leg_swing // 2
	draw_soccer_ball(screen, ball_x, feet_y - 8, 8, game.frame_count * 10)

	# 名字顯示在頭上
	draw_text(screen, fonts['small'], settings['player_name'], config.text_color, x, feet_y - 108, 'center')


# 用幾何圖形畫出球員的身體：腳、短褲、球衣、背號、頭。
# (x, feet_y) 是腳底的中間；leg_swing 是兩隻腳前後分開多少，做出跑步的樣子。
def draw_player_body(screen, fonts, settings, x, feet_y, leg_swing):
	# 腳（皮膚）與鞋子
	pygame.draw.rect(screen, config.skin_color, (x - 4 + leg_swing, feet_y - 26, 8, 26))
	pygame.draw.rect(screen, config.skin_color, (x - 4 - leg_swing, feet_y - 26, 8, 26))
	pygame.draw.rect(screen, config.shoe_color, (x - 4 + leg_swing, feet_y - 6, 13, 6))
	pygame.draw.rect(screen, config.shoe_color, (x - 4 - leg_swing, feet_y - 6, 13, 6))

	# 短褲
	pygame.draw.rect(screen, config.shorts_color, (x - 14, feet_y - 36, 28, 14))

	# 球衣與手臂
	pygame.draw.rect(screen, settings['jersey_rgb'], (x - 16, feet_y - 64, 32, 30))
	pygame.draw.rect(screen, settings['jersey_rgb'], (x - 22, feet_y - 62, 7, 14))
	pygame.draw.rect(screen, settings['jersey_rgb'], (x + 15, feet_y - 62, 7, 14))
	pygame.draw.rect(screen, config.skin_color, (x - 22, feet_y - 48, 7, 10))
	pygame.draw.rect(screen, config.skin_color, (x + 15, feet_y - 48, 7, 10))

	# 背號：淺色球衣用黑字，深色球衣用白字，才看得清楚
	jersey_rgb = settings['jersey_rgb']
	if jersey_rgb[0] + jersey_rgb[1] + jersey_rgb[2] > 450:
		number_color = config.black
	else:
		number_color = config.white
	number_image = fonts['number'].render(settings['jersey_number'], True, number_color)
	number_rect = number_image.get_rect()
	number_rect.center = (x, feet_y - 49)
	screen.blit(number_image, number_rect)

	# 頭和眼睛（面向右邊）
	pygame.draw.circle(screen, config.skin_color, (x, feet_y - 72), 11)
	pygame.draw.circle(screen, config.black, (x + 5, feet_y - 74), 2)


# ===== 關卡元素 =====

# 依照種類呼叫對應的畫法。只畫在畫面範圍內的，畫面外的畫了也看不到。
def draw_thing(screen, images, thing, camera_x, frame_count):
	screen_x = int(thing['x'] - camera_x)
	if screen_x < -150 or screen_x > config.screen_width + 50:
		return

	kind = thing['kind']
	# 撿走的球就不畫了
	if kind == 'ball' and thing['done']:
		return

	# 有這種角色的圖片就用圖片
	if kind in images:
		draw_image(screen, images[kind], screen_x, get_thing_bottom(thing))
		return

	if kind == 'cone':
		draw_cone(screen, screen_x)
	elif kind == 'defender':
		draw_defender(screen, screen_x, thing['lift'], frame_count)
	elif kind == 'ball':
		radius = config.ball_radius
		draw_soccer_ball(screen, screen_x + radius, config.ground_y - radius, radius, -frame_count * 6)
	elif kind == 'high_ball':
		draw_high_ball(screen, screen_x, frame_count)


# 關卡元素的底部在螢幕上的高度，畫圖片時用。
# 高空球飄在半空中；其他都站在地上，被踢飛的防守球員再往上加 lift。
def get_thing_bottom(thing):
	if thing['kind'] == 'high_ball':
		return config.high_ball_center_y + config.high_ball_radius
	return config.ground_y - int(thing['lift'])


# 三角錐：橘色三角形，中間一條白色反光帶。
def draw_cone(screen, left):
	width = config.cone_width
	height = config.cone_height
	bottom = config.ground_y
	middle = left + width // 2
	pygame.draw.polygon(screen, config.cone_color, [(left, bottom), (left + width, bottom), (middle, bottom - height)])

	# 反光帶在 40% 到 58% 高度之間；三角形愈高愈窄，所以兩側要依高度往內縮
	low = int(height * 0.40)
	high = int(height * 0.58)
	low_half = (width // 2) * (height - low) // height
	high_half = (width // 2) * (height - high) // height
	stripe = [(middle - low_half, bottom - low), (middle + low_half, bottom - low), (middle + high_half, bottom - high), (middle - high_half, bottom - high)]
	pygame.draw.polygon(screen, config.white, stripe)

	# 底座
	pygame.draw.rect(screen, config.cone_base_color, (left - 4, bottom - 5, width + 8, 5))


# 鏟球的防守球員：身體幾乎躺平，腳往左（朝向我們的球員）伸出去。
# lift 是離地多高：平常是 0，被射門踢飛時會愈來愈大，整個人往上飛走。
def draw_defender(screen, left, lift, frame_count):
	bottom = config.ground_y - int(lift)
	jersey = config.defender_jersey_color

	# 身後揚起的草屑，跟著時間抖動，看起來在滑動；飛起來之後就沒有草屑了
	if lift == 0:
		for i in range(3):
			dust_x = left + 66 + i * 10 + (frame_count + i * 3) % 6
			dust_y = bottom - 6 - (i % 2) * 6
			pygame.draw.circle(screen, config.dust_color, (dust_x, dust_y), 5 - i)

	# 伸出去的腳和鞋子
	pygame.draw.line(screen, config.skin_color, (left + 26, bottom - 14), (left + 4, bottom - 6), 7)
	pygame.draw.rect(screen, config.shoe_color, (left, bottom - 10, 10, 7))
	# 另一隻彎著的腳
	pygame.draw.line(screen, config.skin_color, (left + 30, bottom - 12), (left + 22, bottom - 2), 6)

	# 短褲
	pygame.draw.rect(screen, config.shorts_color, (left + 24, bottom - 20, 16, 12))

	# 身體（斜躺的四邊形）
	body = [(left + 36, bottom - 22), (left + 58, bottom - 30), (left + 62, bottom - 16), (left + 38, bottom - 8)]
	pygame.draw.polygon(screen, jersey, body)

	# 撐地的手臂
	pygame.draw.line(screen, config.skin_color, (left + 50, bottom - 14), (left + 56, bottom - 2), 5)

	# 頭
	pygame.draw.circle(screen, config.skin_color, (left + 64, bottom - 26), 9)
	pygame.draw.circle(screen, config.black, (left + 60, bottom - 28), 2)


# 射出去的球：貼著地面往右飛，左邊拖著速度線。
def draw_shot(screen, images, shot, camera_x, frame_count):
	if 'shot' in images:
		draw_image(screen, images['shot'], shot['x'] - camera_x, config.ground_y)
		return
	radius = config.shot_radius
	center_x = int(shot['x'] - camera_x) + radius
	center_y = config.ground_y - radius
	for i in range(3):
		line_y = center_y - 5 + i * 5
		line_end = center_x - radius - 3
		pygame.draw.line(screen, config.white, (line_end - 16 - i * 4, line_y), (line_end, line_y), 2)
	draw_soccer_ball(screen, center_x, center_y, radius, frame_count * 25)


# 高空球：在頭頂高度飛過來的足球，後面拖著幾條速度線。
def draw_high_ball(screen, left, frame_count):
	radius = config.high_ball_radius
	center_x = left + radius
	center_y = config.high_ball_center_y
	for i in range(3):
		line_y = center_y - 6 + i * 6
		line_start = center_x + radius + 4
		pygame.draw.line(screen, config.white, (line_start, line_y), (line_start + 14 + i * 4, line_y), 2)
	draw_soccer_ball(screen, center_x, center_y, radius, -frame_count * 12)


# ===== 球門 =====

# 側面看到的球門：前柱、橫樑、往後斜下去的球網。球員碰到前柱就算過關。
def draw_goal(screen, images, goal_screen_x):
	if goal_screen_x < -150 or goal_screen_x > config.screen_width + 50:
		return
	front = int(goal_screen_x)
	if 'goal' in images:
		draw_image(screen, images['goal'], front, config.ground_y)
		return
	depth = 80
	height = 150
	bottom = config.ground_y
	top = bottom - height

	# 球網：直線和橫線組成的格子
	for x in range(front, front + depth + 1, 10):
		pygame.draw.line(screen, config.net_color, (x, top), (x, bottom), 1)
	for y in range(top, bottom + 1, 12):
		pygame.draw.line(screen, config.net_color, (front, y), (front + depth, y), 1)

	# 門柱和橫樑
	pygame.draw.line(screen, config.white, (front, bottom), (front, top), 6)
	pygame.draw.line(screen, config.white, (front, top), (front + depth, top), 6)
	pygame.draw.line(screen, config.white, (front + depth, top), (front + depth, bottom), 3)


# ===== 畫面上的資訊 =====

# 一顆愛心：兩個圓加一個倒三角形。
def draw_heart(screen, x, y):
	pygame.draw.circle(screen, config.heart_color, (x - 5, y), 6)
	pygame.draw.circle(screen, config.heart_color, (x + 5, y), 6)
	pygame.draw.polygon(screen, config.heart_color, [(x - 11, y + 2), (x + 11, y + 2), (x, y + 14)])


# 黃底黑字的「官方版本」標籤；(center_x, top) 是標籤上緣的中間。
def draw_official_badge(screen, font, center_x, top):
	text_image = font.render('官方版本', True, config.official_badge_text_color)
	rect = text_image.get_rect()
	rect.midtop = (center_x, top)
	# 底色比文字大一圈
	badge_rect = rect.inflate(28, 10)
	pygame.draw.rect(screen, config.official_badge_color, badge_rect)
	screen.blit(text_image, rect)


def draw_hud(screen, fonts, game, settings):
	# 左上：背號、名字、生命
	title = '#' + settings['jersey_number'] + ' ' + settings['player_name']
	draw_text(screen, fonts['medium'], title, config.text_color, 16, 8, 'left')

	# 生命太多時愛心會排出畫面，所以超過 10 條就改用數字顯示
	if game.lives > 10:
		draw_heart(screen, 30, 60)
		draw_text(screen, fonts['medium'], 'x ' + str(game.lives), config.text_color, 48, 44, 'left')
	else:
		# 學生可能把命改成小數（例如減 0.5），range 只收整數，所以先用 int 去掉小數
		for i in range(int(game.lives)):
			draw_heart(screen, 30 + i * 28, 60)

	# 右上：分數、速度、彈藥。顯示速度是為了讓學生看到 on_tick 有沒有作用
	right = config.screen_width - 16
	draw_text(screen, fonts['medium'], '分數 ' + str(game.score), config.text_color, right, 8, 'right')
	speed_text = '速度 ' + str(round(game.speed, 1))
	draw_text(screen, fonts['small'], speed_text, config.text_color, right, 46, 'right')
	# 足球圖示畫在數字的左邊；數字位數會變，所以要先知道文字多寬
	ammo_rect = draw_text(screen, fonts['small'], 'x ' + str(game.ammo), config.text_color, right, 72, 'right')
	draw_soccer_ball(screen, ammo_rect.left - 14, ammo_rect.centery, 9, 0)

	# 左下：按鍵提示，學生不用回去翻說明就知道怎麼射門
	draw_text(screen, fonts['small'], '空白鍵 跳　F 射門', config.text_color, 16, config.screen_height - 32, 'left')

	# 官方模式：上方中間標示「官方版本」，讓助教一眼看出這不是學生自己改過的版本
	if game.mode == 'official':
		draw_official_badge(screen, fonts['small'], config.screen_width // 2, 12)
		return

	# 學生模式：下方畫出離球門還有多遠的進度條
	bar_left = 220
	bar_width = config.screen_width - 440
	bar_y = config.screen_height - 22
	pygame.draw.rect(screen, config.progress_back_color, (bar_left, bar_y, bar_width, 10))
	pygame.draw.rect(screen, config.progress_fill_color, (bar_left, bar_y, int(bar_width * game.progress), 10))
	pygame.draw.line(screen, config.white, (bar_left + bar_width, bar_y - 6), (bar_left + bar_width, bar_y + 14), 3)


# 遊戲結束時，在畫面上蓋一層半透明的黑色，再寫上結果。
def draw_end_screen(screen, fonts, game, settings):
	overlay = pygame.Surface((config.screen_width, config.screen_height))
	overlay.fill(config.black)
	# set_alpha 讓整張圖變半透明，舊版 pygame 也支援。
	# 官方模式要投影給助教看，遮得更暗，背後的畫面才不會干擾名字和分數
	if game.mode == 'official':
		overlay.set_alpha(235)
	else:
		overlay.set_alpha(170)
	screen.blit(overlay, (0, 0))

	center_x = config.screen_width // 2

	# 官方模式的結束畫面要方便助教登記，所以名字和分數用最大的字
	if game.mode == 'official':
		draw_official_badge(screen, fonts['medium'], center_x, 30)
		name_text = '#' + settings['jersey_number'] + ' ' + settings['player_name']
		draw_text(screen, fonts['huge'], name_text, config.text_color, center_x, 110, 'center')
		draw_text(screen, fonts['huge'], str(game.score) + ' 分', config.win_color, center_x, 230, 'center')
		draw_text(screen, fonts['small'], '按 R 或 Enter 再玩一次，按 Esc 離開', config.text_color, center_x, 400, 'center')
		return

	if game.result == 'win':
		draw_text(screen, fonts['huge'], '過關！', config.win_color, center_x, 70, 'center')
	else:
		draw_text(screen, fonts['huge'], '遊戲結束', config.lose_color, center_x, 70, 'center')

	name_text = '#' + settings['jersey_number'] + ' ' + settings['player_name']
	draw_text(screen, fonts['large'], name_text, config.text_color, center_x, 190, 'center')
	draw_text(screen, fonts['large'], '分數 ' + str(game.score), config.text_color, center_x, 255, 'center')
	draw_text(screen, fonts['small'], '按 R 或 Enter 再玩一次，按 Esc 離開', config.text_color, center_x, 360, 'center')
