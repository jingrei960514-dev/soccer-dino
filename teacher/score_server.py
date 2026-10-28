# 官方比賽的計分板伺服器。在要投影的老師電腦上執行：
#	python teacher/score_server.py
# 執行後用這台電腦的瀏覽器打開 http://localhost:8765 就是計分板。
# 學生在 official.ipynb 填上這台電腦的 IP 和比賽代碼，每玩完一局，分數就會自動送過來，每個人只保留最高分。
# 只用 Python 內建的模組，不用另外安裝套件；按 Ctrl + C 關閉。
#
# 安全上的取捨：學生在 notebook 裡可以執行任何 Python，所以沒辦法完全防止送假分數。
# 這裡只擋掉「不小心」和「太明顯」的情況：比賽代碼不對、關卡種子不同（改過 config.py）、分數大得不合理。
# 刪除和清除只有這台電腦自己能做，學生的電腦只能送分數。

import http.server
import json
import os
import random
import socket
import sys

# 把專案最外層加進 Python 找檔案的地方，才能用 from soccer import config 讀到連接埠和關卡種子
teacher_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(teacher_folder))
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from soccer import config

scoreboard_path = os.path.join(teacher_folder, 'scoreboard.html')
# 分數存成檔案，伺服器關掉再打開、或電腦當機，名單和比賽代碼都還在
data_path = os.path.join(teacher_folder, 'scores.json')
# 名字最長多少字：「#」、背號、空格、名字
max_label_length = 1 + config.max_number_length + 1 + config.max_name_length
# 學生送過來的資料最多讀多少位元組；正常一筆不到 200，太大的直接拒絕
max_body_size = 2000


# ===== 讀寫分數檔 =====

def make_match_code():
	return str(random.randint(1000, 9999))


# 檔案不存在或壞掉時，從空白名單和一組新的比賽代碼開始
def load_data():
	try:
		with open(data_path, encoding='utf-8') as data_file:
			return json.load(data_file)
	except (OSError, ValueError):
		return {'code': make_match_code(), 'records': []}


# 先寫到暫存檔再換名字：寫到一半當機的話，原本的檔案還是完整的
def save_data():
	temp_path = data_path + '.tmp'
	with open(temp_path, 'w', encoding='utf-8') as data_file:
		json.dump(data, data_file, ensure_ascii=False, indent=1)
	os.replace(temp_path, data_path)


data = load_data()
save_data()


# ===== 分數的規則 =====

def find_record(name):
	for record in data['records']:
		if record['name'] == name:
			return record
	return None


# 同一個人玩好幾次時只留最高分。回傳 'new'（第一次登記）、'better'（刷新紀錄）或 'lower'（沒有比較高），
# 以及這個人目前的最高分；計分板和學生的遊戲畫面都用這兩個值寫出提示
def add_score(name, score):
	record = find_record(name)
	if record is None:
		data['records'].append({'name': name, 'score': score})
		result = 'new'
	elif score > record['score']:
		record['score'] = score
		result = 'better'
	else:
		result = 'lower'
	save_data()
	best = find_record(name)['score']
	print(name + '　' + str(score) + ' 分　' + result)
	return {'result': result, 'best': best}


# 檢查學生的遊戲送過來的資料，有問題回傳要給學生看的中文說明，沒問題回傳空字串
def check_submission(body):
	if not isinstance(body, dict):
		return '送過來的資料格式不對，請助教手動登記。'
	if str(body.get('code', '')) != data['code']:
		return '比賽代碼不對，請照著計分板上的代碼改 match_code。'
	if body.get('seed') != config.official_seed:
		return '關卡和官方版本不一樣，這筆分數不算。請用助教發的檔案重新玩。'
	name = body.get('name')
	if not isinstance(name, str) or name.strip() == '' or len(name) > max_label_length:
		return '名字的格式不對，請助教手動登記。'
	score = body.get('score')
	# bool 在 Python 裡也算整數，要排除
	if isinstance(score, bool) or not isinstance(score, int) or score < 0 or score > config.max_official_score:
		return '分數不合理，請助教手動登記。'
	return ''


# ===== 找出這台電腦的 IP =====

# 學生要連的是這台電腦在區域網路裡的 IP，例如 192.168.1.23。
# 一台電腦可能有好幾個（有線、無線、虛擬網卡），全部列出來，讓老師挑學生連得到的那一個
def find_addresses():
	addresses = []
	# 這個方法會問作業系統「要連到外面時用哪張網卡」，通常就是學生連得到的那個 IP。
	# UDP 的 connect 不會真的送出任何資料，所以沒有網路也不會卡住
	try:
		probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		probe.connect(('10.255.255.255', 1))
		addresses.append(probe.getsockname()[0])
		probe.close()
	except OSError:
		pass
	try:
		for address in socket.gethostbyname_ex(socket.gethostname())[2]:
			if address not in addresses and not address.startswith('127.'):
				addresses.append(address)
	except OSError:
		pass
	return addresses


# ===== 處理連線 =====

class ScoreHandler(http.server.BaseHTTPRequestHandler):
	# 伺服器一次只處理一個連線，所以某台電腦連上之後不送資料，最多等幾秒就放棄，其他人才不會被卡住
	timeout = 5

	# 只有這台電腦自己打開的計分板，才可以手動加分、刪除、清除，以及看到比賽代碼
	def is_local(self):
		return self.client_address[0] in ['127.0.0.1', '::1']

	def send_json(self, status, value):
		body = json.dumps(value, ensure_ascii=False).encode('utf-8')
		self.send_response(status)
		self.send_header('Content-Type', 'application/json; charset=utf-8')
		self.send_header('Content-Length', str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def send_error_message(self, status, text):
		self.send_json(status, {'error': text})

	# 讀出 POST 送來的 JSON；讀不出來回傳 None
	def read_json(self):
		try:
			length = int(self.headers.get('Content-Length', '0'))
		except ValueError:
			return None
		if length <= 0 or length > max_body_size:
			return None
		try:
			return json.loads(self.rfile.read(length).decode('utf-8'))
		except ValueError:
			return None

	def do_GET(self):
		if self.path == '/' or self.path == '/scoreboard.html':
			with open(scoreboard_path, 'rb') as page_file:
				body = page_file.read()
			self.send_response(200)
			self.send_header('Content-Type', 'text/html; charset=utf-8')
			self.send_header('Content-Length', str(len(body)))
			self.end_headers()
			self.wfile.write(body)
		elif self.path == '/api/scores':
			reply = {'records': data['records']}
			# 比賽代碼只給投影的那台看，學生直接連進來查不到
			if self.is_local():
				reply['code'] = data['code']
				reply['addresses'] = find_addresses()
			self.send_json(200, reply)
		else:
			self.send_error_message(404, '找不到這個網址。')

	def do_POST(self):
		body = self.read_json()
		if body is None:
			self.send_error_message(400, '送過來的資料格式不對，請助教手動登記。')
			return

		if self.path == '/api/scores':
			# 助教在計分板上手動輸入的，不用比賽代碼和種子
			if self.is_local() and body.get('manual') is True:
				problem = ''
				name = body.get('name')
				score = body.get('score')
				if not isinstance(name, str) or name.strip() == '' or isinstance(score, bool) or not isinstance(score, int) or score < 0:
					problem = '名字或分數的格式不對。'
			else:
				problem = check_submission(body)
			if problem != '':
				self.send_error_message(400, problem)
				return
			self.send_json(200, add_score(body['name'].strip(), body['score']))
			return

		if not self.is_local():
			self.send_error_message(403, '只有計分板那台電腦可以這樣做。')
			return

		if self.path == '/api/delete':
			remaining_records = []
			for record in data['records']:
				if record['name'] != body.get('name'):
					remaining_records.append(record)
			data['records'] = remaining_records
			save_data()
			self.send_json(200, {})
		elif self.path == '/api/clear':
			# 全部清除代表要開始新的一場，順便換一組比賽代碼，上一場的 notebook 就送不進來了
			data['records'] = []
			data['code'] = make_match_code()
			save_data()
			self.send_json(200, {'code': data['code']})
		else:
			self.send_error_message(404, '找不到這個網址。')

	# 預設每個連線都會印一行，計分板每兩秒就問一次，畫面會被洗掉，所以關掉；分數改由 add_score() 印出
	def log_message(self, format, *args):
		pass


def main():
	try:
		# 一次只處理一個連線：每個請求都很短，全班一起送也不會塞車，而且不用擔心兩筆分數同時寫檔
		server = http.server.HTTPServer(('', config.score_server_port), ScoreHandler)
	except OSError:
		print('連接埠 ' + str(config.score_server_port) + ' 已經被占用，可能已經開了另一個計分板伺服器。')
		return

	print('計分板伺服器已經啟動。')
	print('在這台電腦的瀏覽器打開：http://localhost:' + str(config.score_server_port))
	print('學生在 official.ipynb 填寫：')
	for address in find_addresses():
		print('\tscore_server = \'' + address + '\'')
	print('\tmatch_code = \'' + data['code'] + '\'')
	print('第一次執行時 Windows 會問要不要允許 Python 連線，請勾選「私人網路」並允許。')
	print('按 Ctrl + C 關閉。')
	print()
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print('計分板伺服器已關閉，分數存在 ' + data_path)
	server.server_close()


if __name__ == '__main__':
	main()
