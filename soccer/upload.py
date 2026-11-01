# 自動登記分數：官方模式結束一局時，把名字和分數送到老師電腦上的計分板（teacher/score_server.py）。
# 也負責比賽前的「測試連線」：學生先確認連得到計分板，老師在計分板上看到誰已經連上。
# 只用 Python 內建的 urllib 和 json，學生電腦不用多裝任何套件。
# 送不出去時不能讓遊戲出錯，只回傳一句中文說明，畫在結束畫面上，請助教手動登記。

import json
import urllib.error
import urllib.request

from soccer import config


# 把這一局的分數送出去，回傳要畫在結束畫面上的一句話。
# 學生沒有填計分板的 IP 時回傳空字串，代表這一場不用自動登記，結束畫面照舊。
def send_score(settings, score):
	if settings['score_server'] == '':
		return ''

	data = make_data(settings)
	data['score'] = score
	reply = post_to_server(settings, '/api/scores', data)
	if 'error' in reply:
		return reply['error']

	if reply['result'] == 'new':
		return '已登記到排行榜！'
	if reply['result'] == 'better':
		return '刷新紀錄！排行榜已更新'
	return '沒有超過你的最高分 ' + str(reply['best']) + ' 分，排行榜保留原本的分數'


# 比賽前的測試連線：送出名字、比賽代碼和種子，但不送分數。
# 回傳 (成功與否, 要印給學生看的一句話)；成功的話，計分板的「已連線」名單會出現這個名字。
def check_connection(settings):
	reply = post_to_server(settings, '/api/hello', make_data(settings))
	# 比賽還沒開始，連不到時不用急著找助教手動登記，先請學生檢查 IP
	if 'unreachable' in reply:
		return False, '連不到計分板：score_server 可能抄錯，或計分板還沒打開。'
	if 'error' in reply:
		return False, reply['error']
	return True, '連線成功！計分板上已經出現「' + settings['player_label'] + '」，玩完一局分數就會自動登記。'


# 分數和測試連線都要帶的資料
def make_data(settings):
	data = {}
	data['name'] = settings['player_label']
	data['code'] = settings['match_code']
	# 計分板會比對種子：學生改過 config.py 的關卡，或拿到舊版的檔案，分數就不算數
	data['seed'] = config.official_seed
	return data


# 把 data 送到計分板的 path，回傳計分板的回覆。
# 送不出去或被拒絕時，回傳 {'error': 中文說明}，呼叫的地方只要檢查有沒有 'error' 就好；
# 完全連不到時再多一個 'unreachable'，測試連線用它換成比較適合的說明
def post_to_server(settings, path, data):
	server = settings['score_server']
	# 學生只填 IP 時，自動加上連接埠；學生自己寫了 IP:連接埠 就照用
	if ':' not in server:
		server = server + ':' + str(config.score_server_port)
	url = 'http://' + server + path

	body = json.dumps(data).encode('utf-8')
	request = urllib.request.Request(url, body, {'Content-Type': 'application/json'})

	try:
		with urllib.request.urlopen(request, timeout=config.score_upload_timeout) as response:
			return json.loads(response.read().decode('utf-8'))
	except urllib.error.HTTPError as error:
		# 計分板有收到，但不接受這筆資料，例如比賽代碼不對；理由由計分板寫好放在 error 裡
		try:
			return {'error': json.loads(error.read().decode('utf-8'))['error']}
		except Exception:
			return {'error': '計分板不接受這筆資料，請助教手動登記。'}
	except Exception:
		# 連不到：IP 打錯、計分板沒開、防火牆擋住、不在同一個網路……學生沒辦法自己處理，交給助教
		return {'error': '連不到計分板，請助教手動登記。', 'unreachable': True}
