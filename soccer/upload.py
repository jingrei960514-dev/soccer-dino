# 自動登記分數：官方模式結束一局時，把名字和分數送到老師電腦上的計分板（teacher/score_server.py）。
# 只用 Python 內建的 urllib 和 json，學生電腦不用多裝任何套件。
# 送不出去時不能讓遊戲出錯，只回傳一句中文說明，畫在結束畫面上，請助教手動登記。

import json
import urllib.error
import urllib.request

from soccer import config


# 把這一局的分數送出去，回傳要畫在結束畫面上的一句話。
# 學生沒有填計分板的 IP 時回傳空字串，代表這一場不用自動登記，結束畫面照舊。
def send_score(settings, score):
	server = settings['score_server']
	if server == '':
		return ''

	# 學生只填 IP 時，自動加上連接埠；學生自己寫了 IP:連接埠 就照用
	if ':' not in server:
		server = server + ':' + str(config.score_server_port)
	url = 'http://' + server + '/api/scores'

	data = {}
	data['name'] = settings['player_label']
	data['score'] = score
	data['code'] = settings['match_code']
	# 計分板會比對種子：學生改過 config.py 的關卡，或拿到舊版的檔案，分數就不算數
	data['seed'] = config.official_seed
	body = json.dumps(data).encode('utf-8')
	request = urllib.request.Request(url, body, {'Content-Type': 'application/json'})

	try:
		with urllib.request.urlopen(request, timeout=config.score_upload_timeout) as response:
			reply = json.loads(response.read().decode('utf-8'))
	except urllib.error.HTTPError as error:
		# 計分板有收到，但不接受這筆分數，例如比賽代碼不對；理由由計分板寫好放在 error 裡
		try:
			reply = json.loads(error.read().decode('utf-8'))
			return reply['error']
		except Exception:
			return '計分板不接受這筆分數，請助教手動登記。'
	except Exception:
		# 連不到：IP 打錯、計分板沒開、防火牆擋住、不在同一個網路……學生沒辦法自己處理，交給助教
		return '連不到計分板，請助教手動登記。'

	if reply['result'] == 'new':
		return '已登記到排行榜！'
	if reply['result'] == 'better':
		return '刷新紀錄！排行榜已更新'
	return '沒有超過你的最高分 ' + str(reply['best']) + ' 分，排行榜保留原本的分數'
