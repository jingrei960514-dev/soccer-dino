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


# ===== 陰影 =====

# 在地面上畫一個半透明的橢圓形陰影。center_x 是陰影中間的 x，width 是東西貼地時陰影的寬度，
# height_above_ground 是東西的底部離地多高。陰影永遠畫在地面上，東西愈高陰影愈小。
# 要在東西本身之前畫，陰影才會被東西蓋住。
def draw_shadow(screen, center_x, width, height_above_ground):
	scale = 1 - height_above_ground / config.shadow_fade_height
	scale = max(config.shadow_min_scale, min(1, scale))
	shadow_width = max(2, int(width * scale))
	shadow_height = max(2, shadow_width // config.shadow_flatness)

	# pygame.draw.ellipse 直接畫在畫面上不能半透明，
	# 所以先畫在一張支援透明的小圖上（SRCALPHA），再貼到畫面
	shadow_image = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
	color = (config.shadow_color[0], config.shadow_color[1], config.shadow_color[2], config.shadow_alpha)
	pygame.draw.ellipse(shadow_image, color, (0, 0, shadow_width, shadow_height))
	rect = shadow_image.get_rect()
	rect.center = (int(center_x), config.ground_y)
	screen.blit(shadow_image, rect)


# 關卡元素的陰影，依種類決定寬度和離地高度。
def draw_thing_shadow(screen, thing, screen_x):
	kind = thing['kind']
	if kind == 'cone':
		draw_shadow(screen, screen_x + config.cone_width // 2, config.cone_width + 10, 0)
	elif kind == 'defender':
		# 被踢飛時 lift 愈來愈大，陰影就跟著縮小
		draw_shadow(screen, screen_x + config.defender_width // 2, config.defender_width, thing['lift'])
	elif kind == 'ball':
		radius = config.ball_radius
		draw_shadow(screen, screen_x + radius, radius * 2 + 4, 0)
	elif kind == 'shoe':
		size = config.flying_shoe_size
		draw_shadow(screen, screen_x + size // 2, size, config.ground_y - config.flying_shoe_bottom)


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

# 側面球員的三種姿勢：跑步的第 0 格、第 1 格，以及在空中的 'jump'。
# 每隻手腳是一串關節的位置 [肩膀或臀部, 手肘或膝蓋, 手或腳踝]，
# 數字是相對於「腳底中間」(x, feet_y) 往右、往下各差幾像素，所以負的 y 代表往上。
# near 是靠近鏡頭的手腳，far 是另一邊被身體擋住一半的手腳。
# 兩格跑步動作：第 0 格兩腳大步張開，第 1 格兩腳收在身體下面、近的膝蓋往前抬。
# 如果兩格只是把前後腳交換，側面看起來外形一模一樣，就看不出在跑，所以兩格的外形要不同。
# 手和同一邊的腳反方向擺
player_poses = {
	0: {
		'near_leg': [(2, -28), (9, -16), (12, -3)],
		'far_leg': [(-2, -28), (-6, -15), (-14, -7)],
		'near_arm': [(0, -53), (-6, -44), (-3, -36)],
		'far_arm': [(0, -53), (7, -46), (13, -42)],
	},
	1: {
		'near_leg': [(1, -28), (10, -20), (3, -11)],
		'far_leg': [(-1, -28), (2, -15), (1, -3)],
		'near_arm': [(0, -53), (6, -45), (12, -41)],
		'far_arm': [(0, -53), (-5, -45), (-2, -37)],
	},
	# 跳起來時兩腳收起來，手往前上方伸
	'jump': {
		'near_leg': [(2, -28), (11, -21), (6, -8)],
		'far_leg': [(-2, -28), (3, -17), (-8, -11)],
		'near_arm': [(0, -53), (8, -58), (14, -65)],
		'far_arm': [(0, -53), (-7, -47), (-12, -42)],
	},
}


def draw_player(screen, fonts, images, game, settings):
	x = config.player_x
	feet_y = int(game.player_y)

	# 在地上時兩格跑步動作輪流；在空中時固定成跳躍的姿勢
	if game.on_ground:
		pose = player_poses[(game.frame_count // config.run_frame_length) % 2]
	else:
		pose = player_poses['jump']

	# 腳前帶著的球：放在比較前面那隻腳的腳尖前方，跟著步伐前後動
	front_foot_x = max(pose['near_leg'][2][0], pose['far_leg'][2][0])
	ball_radius = 8
	ball_x = x + front_foot_x + 10 + ball_radius

	# 陰影留在地面上，跳得愈高愈小。畫在閃爍的判斷之前，無敵閃爍時陰影仍然看得到，
	# 玩家才不會找不到自己在哪裡
	height_above_ground = config.ground_y - feet_y
	draw_shadow(screen, x, config.player_width + 8, height_above_ground)
	draw_shadow(screen, ball_x, ball_radius * 2 + 2, height_above_ground)

	# 無敵時閃爍：每 6 幀換一次「畫」或「不畫」
	if game.invincible_timer > 0 and (game.invincible_timer // 6) % 2 == 0:
		return

	# 有 player.png 就用圖片，圖片的底部中間對準球員的腳。
	# 注意：用圖片時看不到學生選的球衣顏色和背號，因為那些畫在圖片裡了
	if 'player' in images:
		image_width = config.image_sizes['player'][0]
		draw_image(screen, images['player'], x - image_width // 2, feet_y)
	else:
		draw_player_body(screen, fonts, settings, x, feet_y, pose)

	draw_soccer_ball(screen, ball_x, feet_y - ball_radius, ball_radius, game.frame_count * 10)

	# 名字顯示在頭上
	draw_text(screen, fonts['small'], settings['player_name'], config.text_color, x, feet_y - 108, 'center')


# 把 player_poses 裡的相對位置換成螢幕上的座標。
def get_joints(points, x, feet_y):
	joints = []
	for point in points:
		joints.append((x + point[0], feet_y + point[1]))
	return joints


# 一隻腳：大腿和小腿是粗線，腳踝的位置畫一隻往右的鞋子。
def draw_leg(screen, points, x, feet_y, skin):
	joints = get_joints(points, x, feet_y)
	pygame.draw.line(screen, skin, joints[0], joints[1], 7)
	pygame.draw.line(screen, skin, joints[1], joints[2], 6)
	# 膝蓋畫一個圓，大腿和小腿接起來的地方才不會有缺角
	pygame.draw.circle(screen, skin, joints[1], 3)
	ankle = joints[2]
	pygame.draw.rect(screen, config.shoe_color, (ankle[0] - 3, ankle[1] - 3, 12, 6), 0, 2)


# 一隻手：上臂是球衣的袖子，前臂是皮膚。
def draw_arm(screen, points, x, feet_y, sleeve, skin):
	joints = get_joints(points, x, feet_y)
	pygame.draw.line(screen, sleeve, joints[0], joints[1], 7)
	pygame.draw.line(screen, skin, joints[1], joints[2], 5)
	pygame.draw.circle(screen, skin, joints[2], 3)


# 背號的顏色：淺色球衣用黑字，深色球衣用白字，才看得清楚。
def get_number_color(jersey_rgb):
	if jersey_rgb[0] + jersey_rgb[1] + jersey_rgb[2] > 450:
		return config.black
	return config.white


# 用幾何圖形畫出面向右方的側面球員：手腳、短褲、球衣、背號、頭。
# (x, feet_y) 是腳底的中間；pose 是 player_poses 裡的一種姿勢。
# 由遠到近畫：遠的手腳 → 身體 → 近的手腳 → 頭，後畫的會蓋住先畫的。
def draw_player_body(screen, fonts, settings, x, feet_y, pose):
	jersey_rgb = settings['jersey_rgb']

	# 遠的那一邊：顏色暗一點，看起來在身體後面
	draw_arm(screen, pose['far_arm'], x, feet_y, jersey_rgb, config.far_skin_color)
	draw_leg(screen, pose['far_leg'], x, feet_y, config.far_skin_color)

	# 短褲和球衣（側面看比正面窄），四個角稍微圓一點
	pygame.draw.rect(screen, config.shorts_color, (x - 11, feet_y - 35, 22, 11), 0, 3)
	pygame.draw.rect(screen, jersey_rgb, (x - 12, feet_y - 59, 24, 27), 0, 5)

	# 近的那一邊
	draw_leg(screen, pose['near_leg'], x, feet_y, config.skin_color)
	draw_arm(screen, pose['near_arm'], x, feet_y, jersey_rgb, config.skin_color)

	# 背號畫在近的手臂之後：手臂擺過球衣中間時，背號才不會被擋住
	number_image = fonts['number'].render(settings['jersey_number'], True, get_number_color(jersey_rgb))
	# 三位數的背號比側面的球衣寬，等比例縮小到放得進球衣
	max_number_width = 22
	if number_image.get_width() > max_number_width:
		new_height = number_image.get_height() * max_number_width // number_image.get_width()
		number_image = pygame.transform.smoothscale(number_image, (max_number_width, new_height))
	number_rect = number_image.get_rect()
	number_rect.center = (x, feet_y - 45)
	screen.blit(number_image, number_rect)

	# 脖子
	pygame.draw.rect(screen, config.skin_color, (x - 3, feet_y - 63, 7, 6))
	# 頭：先畫頭髮的圓，再把臉的圓往右下錯開蓋上去，頭頂和後腦就會留下頭髮
	pygame.draw.circle(screen, config.hair_color, (x + 1, feet_y - 73), 11)
	pygame.draw.circle(screen, config.skin_color, (x + 3, feet_y - 69), 10)
	# 眼睛和鼻子都在右邊，代表面向右方
	pygame.draw.circle(screen, config.black, (x + 8, feet_y - 71), 2)
	pygame.draw.polygon(screen, config.skin_color, [(x + 12, feet_y - 70), (x + 16, feet_y - 66), (x + 12, feet_y - 64)])


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

	# 陰影先畫，才會被東西本身蓋住；用圖片時也一樣要有陰影
	draw_thing_shadow(screen, thing, screen_x)

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
	elif kind == 'shoe':
		draw_flying_shoe(screen, screen_x, frame_count)


# 關卡元素的底部在螢幕上的高度，畫圖片時用。
# 球鞋飄在半空中；其他都站在地上，被踢飛的防守球員再往上加 lift。
def get_thing_bottom(thing):
	if thing['kind'] == 'shoe':
		return config.flying_shoe_bottom
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
	radius = config.shot_radius
	draw_shadow(screen, shot['x'] - camera_x + radius, radius * 2 + 4, 0)
	if 'shot' in images:
		draw_image(screen, images['shot'], shot['x'] - camera_x, config.ground_y)
		return
	center_x = int(shot['x'] - camera_x) + radius
	center_y = config.ground_y - radius
	for i in range(3):
		line_y = center_y - 5 + i * 5
		line_end = center_x - radius - 3
		pygame.draw.line(screen, config.white, (line_end - 16 - i * 4, line_y), (line_end, line_y), 2)
	draw_soccer_ball(screen, center_x, center_y, radius, frame_count * 25)


# 飛過來的球鞋：在頭頂高度邊翻轉邊飛過來，後面拖著幾條速度線。
# 先把鞋子畫在一張透明的小畫布上（鞋尖朝左，也就是飛過來的方向），再整張旋轉後貼到畫面上。
def draw_flying_shoe(screen, left, frame_count):
	size = config.flying_shoe_size
	center_x = left + size // 2
	center_y = config.flying_shoe_bottom - size // 2

	# 速度線不跟著轉，固定拖在右後方
	for i in range(3):
		line_y = center_y - 6 + i * 6
		line_start = left + size + 4
		pygame.draw.line(screen, config.white, (line_start, line_y), (line_start + 14 + i * 4, line_y), 2)

	shoe = pygame.Surface((size, size), pygame.SRCALPHA)
	# 鞋面：左邊是低低圓圓的鞋尖，往右愈來愈高，最右邊是鞋跟和鞋口
	upper = [(2, 19), (3, 15), (11, 13), (17, 8), (27, 8), (28, 12), (28, 19)]
	pygame.draw.polygon(shoe, config.flying_shoe_color, upper)
	pygame.draw.polygon(shoe, config.flying_shoe_outline_color, upper, 1)
	# 白色線條和鞋帶
	pygame.draw.line(shoe, config.white, (13, 17), (23, 12), 2)
	for lace_x, lace_y in [(8, 14), (11, 13), (14, 11)]:
		pygame.draw.circle(shoe, config.white, (lace_x, lace_y), 1)
	# 鞋底和鞋釘
	pygame.draw.rect(shoe, config.flying_shoe_sole_color, (1, 19, 28, 3), 0, 1)
	for stud_x in [4, 10, 20, 25]:
		pygame.draw.rect(shoe, config.flying_shoe_sole_color, (stud_x, 22, 3, 2))

	# 往前翻轉；rotate 之後畫布會變大，所以用中心點對齊，鞋子才不會轉著轉著飄走
	rotated = pygame.transform.rotate(shoe, frame_count * 12 % 360)
	screen.blit(rotated, rotated.get_rect(center=(center_x, center_y)))


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
