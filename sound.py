# 音效：載入 assets 資料夾裡的音效檔，找不到就用程式產生簡單的「嗶」聲代替。
# 電腦沒有喇叭或音效卡時，pygame 的混音器（mixer）會開不起來，這時就全部靜音，遊戲照常玩。
# engine.py 不直接播放聲音，只把要播的音效名稱放進 game.sounds_to_play，每一幀由主迴圈一起播放。

import array
import math
import os

import pygame

import config


# 必須在 pygame.init() 之前呼叫，設定混音器的格式。
# 最後的 512 是緩衝區大小；預設值比較大，按下跳躍鍵之後要過一下子才聽得到聲音
def prepare_mixer():
	pygame.mixer.pre_init(44100, -16, 2, 512)


# 載入所有音效，回傳一個字典，例如 sounds['jump'] 就是跳躍的聲音。
# 字典是空的代表靜音，播放時查不到名字就什麼都不做，所以不用到處檢查有沒有聲音。
def load_sounds():
	sounds = {}
	if not config.sound_enabled:
		return sounds
	# 混音器沒開起來時 get_init() 會回傳 None
	if pygame.mixer.get_init() is None:
		return sounds

	for name in config.sound_files:
		sound = load_sound_file(config.sound_files[name])
		if sound is None:
			sound = make_beep(config.beep_notes[name])
		# 兩種方法都失敗（例如混音器的格式不支援）就跳過這個音效
		if sound is None:
			continue
		sound.set_volume(config.sound_volume)
		sounds[name] = sound
	return sounds


# 讀取 assets 裡的一個音效檔。檔案不存在或讀不出來就回傳 None，改用嗶聲。
def load_sound_file(file_name):
	path = os.path.join(config.assets_path, file_name)
	if not os.path.exists(path):
		return None
	try:
		return pygame.mixer.Sound(path)
	except pygame.error:
		print('assets 裡的 ' + file_name + ' 讀不出來，改用內建的聲音。請確認它是 wav 或 ogg 音效檔。')
		return None


# 用程式產生一段由好幾個音組成的嗶聲。notes 是 [[頻率, 毫秒], ……]。
# 聲音其實就是一串數字：每秒 44100 個，代表喇叭在每個瞬間要推出去多少。
# 用正弦函數 sin 產生上下起伏的數字，起伏愈快（頻率愈高）聽起來愈尖。
def make_beep(notes):
	# get_init() 回傳（每秒幾個數字, 每個數字的格式, 聲道數）
	mixer_format = pygame.mixer.get_init()
	samples_per_second = mixer_format[0]
	sample_format = mixer_format[1]
	channels = mixer_format[2]
	# 這裡只會產生「有正負號的 16 位元整數」這種格式；混音器用別的格式時就不產生，改成靜音
	if sample_format != -16:
		return None

	# array 是 Python 內建的「固定型別清單」，'h' 代表每個元素都是 16 位元整數，
	# 最後可以直接轉成 pygame 需要的一串位元組
	samples = array.array('h')
	for note in notes:
		pitch = note[0]
		sample_count = int(samples_per_second * note[1] / 1000)
		for i in range(sample_count):
			# 每個音從大聲慢慢變小聲，音和音之間才不會有「啪」的雜音
			fade = 1 - i / sample_count
			value = int(math.sin(2 * math.pi * pitch * i / samples_per_second) * 12000 * fade)
			# 立體聲要左右聲道各放一次
			for channel in range(channels):
				samples.append(value)
	return pygame.mixer.Sound(buffer=samples.tobytes())


# 播放這一幀累積的所有音效。查不到的名字（靜音或載入失敗）就跳過。
def play_sounds(sounds, names):
	for name in names:
		if name in sounds:
			sounds[name].play()
