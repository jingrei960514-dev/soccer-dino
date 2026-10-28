# 測試官方模式的難度：讓電腦自動玩很多局，統計平均能撐多久、拿幾分。
#	python teacher/test_official.py          玩 30 局
#	python teacher/test_official.py 100      玩 100 局
# 改了 soccer/config.py 的官方模式數值之後跑一次，就知道變難還是變簡單，不用自己玩好幾遍。
#
# 電腦怎麼玩：每一幀先預測「接下來都不按」會不會撞到；會撞到的話，找出「在哪幾幀按跳躍可以躲過」，
# 這段時間就是這個障礙物的「容許範圍」。人按鍵不會剛好按在正中間，所以實際按下的時間
# 是正中間再加上一點隨機誤差（human_error_frames）。容許範圍愈窄，誤差就愈容易讓它撞到。
# 電腦不會射門，所以算出來的成績比會射門的同學差一點。
#
# 另外會用「完全沒有誤差」的電腦玩一局，確認每個障礙物都躲得掉；這一局撞到了，就代表關卡出現了不公平的組合。

import os
import random
import sys

# 不開視窗、不出聲音，只跑遊戲規則，比真的玩快幾百倍
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
teacher_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(teacher_folder))
from soccer import config
from soccer import engine

# 人按跳躍鍵時，和最好的時機平均差幾幀（標準差）；60 幀 = 1 秒，4 幀大約是 0.07 秒
human_error_frames = 4
# 每一局最多玩幾秒；超過就當作「死不了」，直接結束這一局
max_seconds = 300
# 預測未來幾幀會不會撞到
look_ahead_frames = 90


# ===== 預測 =====
# 為了算得快，這裡用簡化的方式重算一次 engine.py 的跳躍和碰撞，只看球員和障礙物，不看射門。

# 球員和障礙物的碰撞框，回傳 [左, 右, 上, 下]；算法和 engine.py 的 get_player_rect、get_thing_rect 一樣
def player_box(player_y):
	margin = config.hitbox_margin
	left = config.player_x - config.player_width // 2 + margin
	top = int(player_y) - config.player_height + margin
	return [left, left + config.player_width - margin * 2, top, top + config.player_height - margin]


def thing_box(kind, screen_x):
	margin = config.hitbox_margin
	if kind == 'cone':
		width = config.cone_width
		height = config.cone_height
		bottom = config.ground_y
	elif kind == 'defender':
		width = config.defender_width
		height = config.defender_height
		bottom = config.ground_y
	else:
		width = config.flying_shoe_size
		height = width
		bottom = config.flying_shoe_bottom
	left = int(screen_x) + margin
	top = bottom - height + margin
	return [left, left + width - margin * 2, top, top + height - margin]


def boxes_touch(a, b):
	return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


# 把現在的遊戲狀態抄一份簡化版，只留預測需要的東西
def take_snapshot(game):
	snapshot = {}
	snapshot['player_y'] = game.player_y
	snapshot['vy'] = game.vy
	snapshot['jump_count'] = game.jump_count
	snapshot['speed'] = game.speed
	snapshot['things'] = []
	for thing in game.things:
		if thing['done'] or thing['kind'] == 'ball':
			continue
		snapshot['things'].append([thing['kind'], thing['x'] - game.camera_x])
	return snapshot


# 從 snapshot 開始，在 press_frames 裡的那幾幀按跳躍，其他時候都不按，預測 frames 幀。
# 回傳第幾幀會撞到；都不會撞到就回傳 -1
def predict_hit(snapshot, press_frames, frames):
	player_y = snapshot['player_y']
	vy = snapshot['vy']
	jump_count = snapshot['jump_count']
	speed = snapshot['speed']
	things = []
	for pair in snapshot['things']:
		things.append([pair[0], pair[1]])

	for frame in range(frames):
		# 按鍵在更新之前處理，和 engine.py 的主迴圈一樣
		if frame in press_frames and jump_count < 2:
			vy = -config.official_jump_power
			jump_count = jump_count + 1
		vy = engine.keep_in_range(vy + config.gravity, -config.max_up_speed, config.max_fall_speed)
		player_y = player_y + vy
		if player_y >= config.ground_y:
			player_y = config.ground_y
			vy = 0
			jump_count = 0
		if player_y < config.player_height:
			player_y = config.player_height
			vy = 0

		player = player_box(player_y)
		for thing in things:
			thing[1] = thing[1] - speed
			if thing[1] < config.screen_width:
				if thing[0] == 'defender':
					thing[1] = thing[1] - config.defender_extra_speed
				elif thing[0] == 'shoe':
					thing[1] = thing[1] - config.flying_shoe_extra_speed
			if boxes_touch(player, thing_box(thing[0], thing[1])):
				return frame
	return -1


# 決定接下來要在第幾幀按跳躍。回傳「從現在算起再等幾幀」，不用按就回傳 -1。
# 先試只按一次；按一次躲不掉，再試按兩次（二段跳），回傳第一次要按的時間
def plan_jump(snapshot, error):
	hit_frame = predict_hit(snapshot, [], look_ahead_frames)
	if hit_frame == -1:
		return -1

	# 找出按一次就躲得掉的所有時間點，取中間，再加上人的誤差
	good_waits = []
	for wait in range(hit_frame + 1):
		if predict_hit(snapshot, [wait], look_ahead_frames) == -1:
			good_waits.append(wait)
	if len(good_waits) > 0:
		return pick_with_error(good_waits, error)

	# 二段跳：第二下可以在第一下之後的任何時候按。只要找第一下的容許範圍，第二下等飛起來之後再重新規劃
	if snapshot['jump_count'] < 2:
		for wait in range(hit_frame + 1):
			for second in range(wait + 1, wait + 45, 2):
				if predict_hit(snapshot, [wait, second], look_ahead_frames) == -1:
					good_waits.append(wait)
					break
	if len(good_waits) > 0:
		return pick_with_error(good_waits, error)
	# 怎麼按都躲不掉：直接撞上去
	return -1


# 容許範圍取中間，再加上隨機誤差；error 是 0 代表完全沒有誤差
def pick_with_error(good_waits, error):
	middle = good_waits[len(good_waits) // 2]
	wait = middle + round(random.gauss(0, error))
	if wait < 0:
		wait = 0
	return wait


# ===== 玩一局 =====

# 回傳 [撐了幾秒, 分數, 撞到幾次]
def play_one_round(error):
	settings = engine.read_official_settings({})
	game = engine.Game('official')
	hits = 0
	lives_before = game.lives
	# 再等幾幀要按跳躍；-1 代表還沒決定
	press_countdown = -1

	while not game.is_over and game.frame_count < max_seconds * config.fps:
		if press_countdown == -1 and game.jump_count < 2:
			press_countdown = plan_jump(take_snapshot(game), error)
		if press_countdown == 0:
			engine.official_on_jump_key(game)
		if press_countdown >= 0:
			press_countdown = press_countdown - 1

		engine.update_game(game, settings)
		game.sounds_to_play = []
		if game.lives < lives_before:
			hits = hits + 1
			lives_before = game.lives
			# 撞到之後重新規劃，不要照原本已經來不及的計畫按
			press_countdown = -1
	return [game.frame_count / config.fps, game.score, hits]


def main():
	rounds = 30
	if len(sys.argv) > 1:
		rounds = int(sys.argv[1])

	perfect = play_one_round(0)
	print('完全沒有誤差：撐了 ' + str(round(perfect[0])) + ' 秒，' + str(perfect[1]) + ' 分，撞到 ' + str(perfect[2]) + ' 次')
	if perfect[2] > 0:
		print('　→ 沒有誤差也會撞到，代表關卡裡有躲不掉的組合，請調整數值')
	print()

	print('有誤差（' + str(human_error_frames) + ' 幀），玩 ' + str(rounds) + ' 局：')
	seconds_list = []
	score_list = []
	survived = 0
	for i in range(rounds):
		random.seed(i)
		result = play_one_round(human_error_frames)
		seconds_list.append(result[0])
		score_list.append(result[1])
		if result[0] >= max_seconds:
			survived = survived + 1
	seconds_list.sort()
	score_list.sort()
	middle = rounds // 2
	print('　撐的秒數：最短 ' + str(round(seconds_list[0])) + '，中間 ' + str(round(seconds_list[middle])) + '，最長 ' + str(round(seconds_list[-1])))
	print('　分數：　　最低 ' + str(score_list[0]) + '，中間 ' + str(score_list[middle]) + '，最高 ' + str(score_list[-1]))
	print('　玩滿 ' + str(max_seconds) + ' 秒都沒死：' + str(survived) + ' 局')
	print('　分數超過 ' + str(config.school_background_score) + '（換成順安國中）：' + str(count_at_least(score_list, config.school_background_score)) + ' 局')


def count_at_least(values, limit):
	count = 0
	for value in values:
		if value >= limit:
			count = count + 1
	return count


if __name__ == '__main__':
	main()
