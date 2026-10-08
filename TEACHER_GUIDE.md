# 足球小恐龍：教師手冊

給上課的老師和助教看。內容依照使用順序排列：課前準備 → 上課流程 → 參考答案與提示卡 → 錯誤訊息一覽 → 官方比賽 → 常見問題。

程式怎麼寫、每一幀發生什麼事，請看 `ARCHITECTURE.md`。

## 檔案總覽

| 檔案 | 給誰 | 用途 |
| --- | --- | --- |
| `game.ipynb` | 學生 | 壞掉的版本，學生從這裡開始修 |
| `solution.ipynb` | 老師 | 全部修好的版本，也是 `game.ipynb` 的來源 |
| `official.ipynb` | 學生 | 官方比賽用，只能改球員設定 |
| `scoreboard.html` | 助教 | 比賽計分板，用瀏覽器打開後投影 |
| `engine.py`、`config.py`、`drawing.py`、`sound.py`、`checks.py` | 不用打開 | 遊戲引擎，必須和 notebook 放在同一個資料夾 |
| `assets/` | 選用 | 放圖片和音效，說明在 `assets/README.md` |
| `clear_outputs.py` | 老師 | 清除 notebook 的執行結果 |
| `make_game_notebook.py` | 老師 | 修改 `solution.ipynb` 之後，重新產生 `game.ipynb` |
| `run.py` | 開發用 | 不開 Jupyter，直接在終端機執行 notebook |

## 一、課前準備

### 每台電腦都要確認

1. **安裝 Python 和套件**：在終端機執行
	```
	python -m pip install pygame jupyterlab
	```
	開發和測試時用的是 Python 3.10 和 pygame 2.6。程式刻意避開只有新版才有的功能，但其他版本沒有實際測過，現場的版本不同時，請務必照第 4 步試跑一次。
2. **複製整個資料夾**：notebook 和所有 `.py` 檔要放在同一個資料夾，`import engine` 才找得到。
3. **把 Jupyter 設定成用 tab 縮排**：做法見下一節。
4. **試跑一次**：打開 `game.ipynb`，從上到下按 `Shift + Enter` 執行，確認遊戲視窗會跳出來，而且有聲音。
5. **清除執行結果**：試跑之後 notebook 會存下執行結果，交給學生前執行一次：
	```
	python clear_outputs.py
	```
6. **計分板**：用要投影的那台電腦打開 `scoreboard.html`，確認字夠大。

如果一台電腦上有好幾個 Python，Jupyter 可能用到沒裝 pygame 的那一個。遊戲會顯示「這台電腦的 Python 沒有安裝 pygame」，並列出這個 kernel 用的是哪個 Python，照訊息裡的指令安裝，或在 Jupyter 右上角換 kernel 即可。

### 把 Jupyter 設定成用 tab 縮排

notebook 裡的程式都用 tab 縮排。Jupyter 預設按 Tab 鍵會插入 4 個空格，同一個函式裡空格和 tab 混在一起時，Python 會出現 `TabError`，所以要先把編輯器改成用 tab。

**JupyterLab 4 和 Jupyter Notebook 7（兩個共用同一份設定）**

1. 上方選單「Settings」→「Settings Editor」。
2. 左邊找到「CodeMirror」。
3. 「Indentation unit」選「Tab」。

設定電腦很多台時，可以直接建立設定檔，內容是：

```json
{
	"defaultConfig": {
		"indentUnit": "Tab"
	}
}
```

存到 `使用者資料夾/.jupyter/lab/user-settings/@jupyterlab/codemirror-extension/plugin.jupyterlab-settings`（資料夾不存在就自己建立），再重新整理 Jupyter 頁面。

**VS Code**

在 `settings.json` 加上：

```json
"[python]": {
	"editor.insertSpaces": false,
	"editor.detectIndentation": false
}
```

notebook 的程式格也會套用這個設定。

## 二、上課流程（一小時）

| 時間 | 活動 | 重點 |
| --- | --- | --- |
| 0 - 5 分 | 開場 | 介紹遊戲，說明今天要「修好一個壞掉的遊戲」 |
| 5 - 10 分 | 試玩破壞版 | 讓學生自己發現四個問題：跳不起來、撞到沒事、障礙物都一樣、不會加速 |
| 10 - 35 分 | 修四個問題 | 由上到下依序修：問題一（關卡）→ 問題二（跳躍）→ 問題三（撞到）→ 問題四（加速），每修好一個就重玩一次 |
| 35 - 45 分 | 自由修改、挑戰題 | 改名字、球衣、關卡；做得快的同學挑戰二段跳和射門 |
| 45 - 50 分 | 同學互玩 | 互相玩對方設計的關卡 |
| 50 - 60 分 | 官方比賽 | 打開 `official.ipynb`，玩完由助教登記分數 |

時間只是建議，可以依學生的進度調整。

提醒學生兩件事：

- 改完程式之後，要先**重新執行改過的那一格**，再執行最後一格，改動才會生效。
- 遊戲視窗沒出現時，看一下工作列，它可能躲在瀏覽器後面。

## 三、學生會用到的變數與函式

### notebook 裡的設定

| 名稱 | 意思 | 預設值（沒寫時） |
| --- | --- | --- |
| `player_name` | 顯示在球員頭上的名字，最多 12 個字 | `'球員'` |
| `jersey_color` | 球衣顏色，可以用 `'red'`、`'blue'`、`'green'`、`'yellow'`、`'white'`、`'black'`、`'orange'`、`'purple'`、`'pink'`、`'sky'`、`'gray'` | `'red'` |
| `jersey_number` | 背號，最多 3 位數 | `10` |
| `course` | 關卡清單，可以用的名稱見下表，最多 1000 個 | 一個簡單的預設關卡 |
| `jump_power` | 學生自己的變數，在 `on_jump_key` 裡使用，引擎不會直接讀它 | 沒有 |

### 關卡元素

| 名稱 | 是什麼 | 怎麼過 |
| --- | --- | --- |
| `'cone'` | 三角錐 | 跳過去 |
| `'defender'` | 鏟球的防守球員，會往球員衝過來 | 跳過去，或射門把他踢飛 |
| `'shoe'` | 從頭頂高度飛過來的球鞋 | 站著不要跳 |
| `'ball'` | 地上的足球 | 碰到就撿起來，加 50 分和一發彈藥 |
| `'gap'` | 空白 | 什麼都沒有，用來調整間隔 |

### 規則函式

引擎會在特定時機自動呼叫這些函式。每個函式的括號裡都要剛好寫一個 `game`。沒寫的函式就當作什麼都不做，不會報錯。

| 函式 | 什麼時候執行 |
| --- | --- |
| `on_jump_key(game)` | 按下空白鍵、上方向鍵或 W |
| `on_hit(game)` | 撞到三角錐、防守球員或球鞋（撞到之後有 1.5 秒無敵） |
| `on_tick(game)` | 每過一秒 |
| `on_shoot_key(game)` | 按下 F 或 X（挑戰題） |

### game 的屬性

| 寫法 | 意思 | 開始時的值 |
| --- | --- | --- |
| `game.on_ground` | 球員是否站在地上，`True` 或 `False` | `True` |
| `game.vy` | 上下的速度，負數往上、正數往下 | `0` |
| `game.lives` | 剩幾條命 | `3` |
| `game.speed` | 往前跑的速度，畫面每一幀捲動幾像素 | `6` |
| `game.jump_count` | 已經跳了幾次，落地時自動變回 0 | `0` |
| `game.ammo` | 射門的彈藥 | `0` |
| `game.over()` | 讓遊戲結束 | |
| `game.shoot()` | 射出一顆貼地的球，碰到防守球員就把他踢飛（加 30 分） | |

學生把數值設得很極端也沒關係：速度會被限制在 1 到 30 之間，跳躍的速度最多 30，球員不會飛出畫面。

### 按鍵

| 按鍵 | 功能 |
| --- | --- |
| 空白鍵、上方向鍵、W | 跳躍 |
| F、X | 射門 |
| R、Enter | 重新開始 |
| Esc | 關閉視窗 |

## 四、四個問題的參考答案

`game.ipynb` 裡由上到下標了【問題一】到【問題四】。問題一是改清單，問題二到四是填空：把函式裡的 `______` 換成正確的程式。

函式裡只要還有一個 `______` 沒填，引擎就會把整個函式當作「還沒寫」，遊戲照常進行，只是那一項還是壞的。所以學生可以填一題、玩一次，不會因為其他空格還沒填而出錯。還沒填完的函式，在遊戲開始前會列在「【提醒】」裡。

### 【問題一】關卡裡全部都是三角錐

把 `course` 裡的一些 `'cone'` 換成其他名稱，例如：

```python
course = ['cone', 'gap', 'defender', 'ball', 'shoe']
for i in range(3):
	course.append('cone')
	course.append('gap')
```

答案沒有標準，只要用到其他名稱就算修好了。這一題放第一個，是因為它只要改文字，最容易上手。

### 【問題二】按跳躍鍵，球員卻跳不起來

學生拿到的：

```python
def on_jump_key(game):
	if game.______:
		game.vy = ______
```

答案：

```python
def on_jump_key(game):
	if game.on_ground:
		game.vy = -jump_power
```

- 為什麼是負數：螢幕的 y 座標是往下增加的，往上跳要讓 y 變小。
- 為什麼要檢查 `game.on_ground`：不檢查的話，在空中一直按會一直往上飛。可以讓學生先把整行改成 `if True:` 玩玩看，再問他們怎麼修。
- 常見錯誤：第二格填成 `jump_power`（忘了負號），球員會往下，看起來像跳不起來。

### 【問題三】撞到障礙物，卻一點事都沒有

學生拿到的：

```python
def on_hit(game):
	game.lives = ______
	if game.lives == ______:
		game.______()
```

答案：

```python
def on_hit(game):
	game.lives = game.lives - 1
	if game.lives == 0:
		game.over()
```

- 常見錯誤：第一格只填 `1` 或 `- 1`。填 `1` 不會出錯，但命永遠是 1；填 `- 1` 命會變成負數，遊戲不會結束。
- 第三格填成 `over` 以外的名字時，會出現「game 沒有 …… 這個屬性，是不是要寫 game.over()？」。

### 【問題四】畫面一直都是同一個速度

學生拿到的：

```python
def on_tick(game):
	game.speed = ______
```

答案：

```python
def on_tick(game):
	game.speed = game.speed + 0.2
```

- 常見錯誤：只填 `0.2`。速度會被限制在最低 1，所以畫面變得很慢，但不會出錯。可以讓學生比較「`0.2`」和「`game.speed + 0.2`」的差別。

### 想調整難度的話

挖空的內容寫在 `make_game_notebook.py` 的 `jump_cell`、`hit_cell`、`tick_cell`。改完執行 `python make_game_notebook.py`，`game.ipynb` 就會重新產生。

- 空格只能放在「一段程式」的位置，例如 `game.lives = ______` 或 `game.______()`。
- 不能把運算子挖掉，例如 `game.lives ______ 1`。這在填之前就是語法錯誤，整格都不能執行。

## 五、挑戰題提示卡

可以印出來發給做得快的同學。

---

### 挑戰一：二段跳

**目標**：球員在空中還可以再跳一次。

**要改哪裡**：【問題二】的 `on_jump_key`。

**可以用的變數**

| 寫法 | 意思 |
| --- | --- |
| `game.jump_count` | 已經跳了幾次。**落地時遊戲會自動把它變回 0** |
| `game.vy` | 上下的速度，負數往上 |

**提示**

1. 原本用 `game.on_ground` 判斷能不能跳，這次改成看 `game.jump_count`。
2. 跳了幾次之內還可以再跳？
3. 每跳一次，`game.jump_count` 要加一。

**參考答案**

```python
def on_jump_key(game):
	if game.jump_count < 2:
		game.vy = -jump_power
		game.jump_count = game.jump_count + 1
```

**再挑戰**：把 2 改成 3 會怎麼樣？

---

### 挑戰二：射門

**目標**：撿到地上的足球就多一發彈藥，按 F 射門，把防守球員踢飛。

**要改哪裡**：在「挑戰題」下面那一格新增一個函式 `on_shoot_key(game)`。按 F 或 X 時遊戲會自動執行它。

**可以用的變數**

| 寫法 | 意思 |
| --- | --- |
| `game.ammo` | 還有幾發彈藥，撿到地上的足球會加一 |
| `game.shoot()` | 射出一顆球 |

**提示**

1. 有彈藥才能射：用 `if` 檢查 `game.ammo`。
2. 射門：呼叫 `game.shoot()`，括號裡不用放東西。
3. 射完彈藥要減一，不然可以無限射。

**參考答案**

```python
def on_shoot_key(game):
	if game.ammo > 0:
		game.shoot()
		game.ammo = game.ammo - 1
```

**補充**：沒寫第 1 和第 3 步也不會出錯，但畫面上同時最多只會有 3 顆球。

---

## 六、錯誤訊息一覽

學生看到的錯誤訊息都在 `checks.py` 和 `engine.py`。訊息分成三種時間點，下面依序列出每一則訊息、原因和處理方法。訊息裡用 `……` 表示會依學生寫的內容替換的部分。

### 開始前的檢查：遊戲視窗不會打開

執行最後一格時，引擎會先檢查設定。有問題時會列出所有問題，標題是「【遊戲沒有開始】請先修正下面的問題」。

| 訊息 | 原因 | 怎麼改 |
| --- | --- | --- |
| player_name 要是文字，前後加上引號…… | 名字不是文字，例如寫成 `player_name = 小明` 或清單 | 前後加引號 |
| player_name 是空的…… | `player_name = ''` | 寫上名字 |
| player_name 太長了，最多 12 個字 | 名字太長會超出畫面 | 縮短 |
| jersey_color 要是文字…… | 顏色沒加引號 | 前後加引號 |
| jersey_color 沒有 '……' 這個顏色。是不是要寫 '……'？ | 顏色名稱打錯或用了大寫 | 照提示改，下一行會列出所有顏色 |
| jersey_number 要是整數…… | 背號是小數或其他東西 | 改成整數 |
| jersey_number 是空的…… | `jersey_number = ''` | 寫一個號碼 |
| jersey_number 太長了，最多 3 位數 | 背號太長會超出球衣 | 縮短 |
| course 要是清單，用中括號把名稱包起來…… | 例如 `course = 'cone'` | 改成 `['cone']` |
| course 是空的清單…… | `course = []` | 至少放一個名稱 |
| course 太長了，有 …… 個，最多 1000 個…… | 迴圈的 `range` 寫太大 | 改小 |
| course 的第 N 個（course[N-1]）是 '……'，引擎不認得這個名稱。是不是要寫 '……'？ | 名稱打錯，例如 `'defnder'`、`'Cone'` | 照提示改，最後一行會列出可以用的名稱 |
| course 的第 N 個……名稱要用引號包起來 | 清單裡放了數字或沒加引號的東西 | 加引號 |
| course 裡還有 …… 個名稱也有問題…… | 打錯的超過 5 個，只列出前 5 個 | 先修前面幾個 |
| …… 應該是函式，要寫成 def ……(game):。 | 例如 `on_tick = 3` | 改成用 `def` 定義 |
| …… 的括號裡要剛好寫一個 game…… | 例如 `def on_hit():` | 括號裡寫 `game` |

### 提醒：遊戲照常開始

標題是「【提醒】遊戲照常開始，但請檢查」。

| 訊息 | 原因 | 怎麼改 |
| --- | --- | --- |
| ……（……時執行）還有 ______ 沒填，遊戲會當作它還沒寫好。 | 函式裡還有空格。引擎不會呼叫這個函式，所以那一項還是壞的 | 把空格填完 |
| 你定義了 ……，但引擎只認得 ……，名字要完全一樣才會被執行。 | 函式名稱打錯，例如 `on_jump`，引擎不會呼叫它 | 改成正確的名稱 |

改好名字之後，Jupyter 還會記得舊名字的函式，所以這個提醒會繼續出現。這時可以忽略，或選「Kernel」→「Restart Kernel」，再從頭執行一次。

### 遊戲中，學生的函式出錯：視窗關掉，印出說明

標題是「【遊戲停止了】你寫的函式出錯了」。說明會列出出錯的函式、出錯的那一行、可能的原因，最後一行是 Python 原本的英文訊息，給助教判斷用。

| 英文錯誤 | 「可能的原因」寫的是 | 常見例子 |
| --- | --- | --- |
| `NameError`（空格） | 還有空格 ______ 沒填，把整個 ______ 換成正確的程式。 | 學生自己另外寫的函式裡還有 `______`；規則函式裡的空格在開始前就會被跳過，不會走到這裡 |
| `NameError` | 用到了 ……，但找不到這個名字。可能是打錯字，或是定義它的那一格還沒執行。是不是要寫 ……？ | `-jump_powr`；或是沒執行 `jump_power = 12` 那一格 |
| `UnboundLocalError` | 在函式裡改了 ……，Python 就把它當成函式自己的新變數，但它還沒有值…… | 在 `on_tick` 裡寫 `jump_power = jump_power + 1` |
| `AttributeError`（自己的變數） | …… 是你自己定義的變數，不是 game 的屬性，前面不用加 game.…… | `game.jump_power` |
| `AttributeError`（game 的屬性） | game 沒有 …… 這個屬性。是不是要寫 game.……？ | `game.live`、`game.speeed` |
| `AttributeError`（其他） | 點後面的名字 …… 不存在，檢查有沒有打錯字。 | |
| `TypeError`（not callable） | 只有函式後面可以加括號…… | `game.speed()` |
| `TypeError`（argument） | 呼叫函式時，括號裡的東西太多或太少…… | `game.over(1)` |
| `TypeError`（文字） | 文字和數字不能直接一起運算…… | `game.speed + '1'` |
| `TypeError`（其他） | 資料的型別不對…… | |
| `ZeroDivisionError` | 除以 0 了…… | |
| `RecursionError` | 函式一直呼叫自己，停不下來…… | 在 `on_hit` 裡呼叫 `on_hit(game)` |
| `IndexError` | 清單裡沒有這個位置…… | |
| `OverflowError` | 數字太大了…… | `game.speed = 10.0 ** 999` |
| 其他 | 程式執行時出錯了，請把這段訊息給助教看。 | 看最後一行的英文訊息 |

### 遊戲中，學生把 game 改壞了：視窗關掉，印出說明

這些寫法本身不會出錯，但遊戲會因此壞掉或沒有反應，所以引擎在學生的函式執行完之後會檢查。

| 標題 | 原因 | 例子 |
| --- | --- | --- |
| 【遊戲停止了】game.…… 不是數字 | `vy`、`lives`、`speed`、`jump_count`、`ammo` 被改成不是數字的東西 | `game.speed = 'fast'` |
| 【遊戲停止了】game.…… 可能打錯字了 | 寫入的屬性名稱和內建的很像，例如 `game.live = ……`。Python 不會報錯，只會多出一個新屬性，結果命永遠不會變少 | `game.vyy = -12` |
| 【遊戲停止了】game.…… 的用法不對 | 把要呼叫的函式當成變數 | `game.over = True` |

學生自己取名、和內建名稱不像的屬性（例如 `game.my_counter`）不會被擋，可以自由使用。

### 其他訊息

| 訊息 | 原因 | 怎麼處理 |
| --- | --- | --- |
| 這台電腦的 Python 沒有安裝 pygame…… | Jupyter 用的 Python 沒有 pygame | 照訊息裡的指令安裝，或換 kernel |
| 最後一格要寫成 engine.run(globals())…… | 最後一格被改掉了 | 改回 `engine.run(globals())` |
| 遊戲被中斷了…… | 在 Jupyter 按了中斷（方塊按鈕） | 不是錯誤，重新執行最後一格就好 |
| assets 裡的 …… 讀不出來，改用幾何圖形 | 圖檔損壞或不是圖片 | 換一張 PNG，或刪掉這個檔案 |
| assets 裡的 …… 讀不出來，改用內建的聲音 | 音效檔損壞或格式不對 | 換成 WAV，或刪掉這個檔案 |

### 引擎抓不到的錯誤

下面這些錯誤發生在執行程式格的時候，還沒輪到引擎，所以會顯示 Python 原本的英文訊息：

| 英文錯誤 | 原因 | 怎麼改 |
| --- | --- | --- |
| `SyntaxError` | 少了冒號、括號沒成對、引號沒成對 | 看錯誤指的那一行和上一行 |
| `IndentationError` | 縮排不對，例如 `def` 下一行沒有縮排 | 函式內容要往右縮一格 |
| `TabError` | 同一段程式裡混用空格和 tab | 刪掉縮排重打，並確認 Jupyter 已設定成用 tab |

另外，學生在函式裡寫出永遠停不下來的迴圈（例如 `while True:`）時，遊戲會卡住不動。這時按 Jupyter 上方的中斷鍵（方塊按鈕）就能停下來，再修改迴圈。

## 七、官方比賽

1. 學生打開 `official.ipynb`，只改球員那一格（名字、球衣、背號），再從上到下執行。
2. 官方版本的規則都已經寫好，而且內建二段跳和射門。關卡用固定的種子產生，每個人遇到的關卡完全一樣，分數才能互相比較。
3. 遊戲結束畫面會用大字顯示「官方版本」、名字和分數。助教看到「官方版本」標籤，才能確定這不是學生自己改過的版本。
4. 助教在 `scoreboard.html` 輸入名字和分數，按 Enter 加入。

### 計分板怎麼用

- 輸入名字和分數，按 Enter 或「加入」。分數打成 `1,230` 也可以。
- 名單自動由高到低排序，前三名放大顯示。同分的人名次相同。
- 同一個名字再登記一次時，只保留比較高的分數，畫面上會顯示「刷新紀錄」或「保留原本的分數」。
- 輸入錯了，按那一列的「刪除」。
- 資料存在這台電腦的瀏覽器裡，重新整理或關掉都不會消失。但換電腦或換瀏覽器就看不到，所以比賽結束記得按「下載 CSV」留存，下載的檔案可以用 Excel 打開。
- 下一場比賽前按「全部清除」。
- 投影時按 F11 全螢幕。

建議名字用「#背號 名字」的格式，例如「#10 小明」，同名的同學才不會被當成同一個人。

## 八、常見問題

| 狀況 | 原因 | 處理 |
| --- | --- | --- |
| 執行最後一格，遊戲視窗沒出現 | 視窗躲在瀏覽器後面 | 看工作列，點遊戲視窗 |
| 視窗出現了，但按鍵沒反應 | 鍵盤焦點還在瀏覽器 | 用滑鼠點一下遊戲視窗 |
| 按 R 沒有反應 | 中文輸入法攔下了按鍵 | 改按 Enter，或把輸入法切成英文 |
| 改了程式，遊戲卻沒變 | 沒有重新執行改過的那一格 | 先執行改過的那一格，再執行最後一格 |
| 刪掉一個函式，遊戲還是照用 | Jupyter 會記住執行過的東西 | 「Kernel」→「Restart Kernel」，再從頭執行 |
| 最後一格一直顯示 `[*]`，不會結束 | 遊戲視窗還開著（可能躲在後面），或程式卡在無窮迴圈 | 找到遊戲視窗按 Esc；找不到就按 Jupyter 的中斷鍵 |
| 按「Run All」跑不起來 | notebook 選到了沒有 pygame 的 kernel | 在右上角換成已安裝 pygame 的 Python |
| 中文變成方框 | 電腦沒有中文字型 | 在 `config.py` 的 `font_names` 加上電腦上有的中文字型名稱 |
| 沒有聲音 | 喇叭沒開；`config.py` 的 `sound_enabled` 是 `False`；或 kernel 還在用更新前的舊程式 | 檢查喇叭和設定，再重新啟動 kernel；全班一起有聲音太吵時，可以把 `sound_enabled` 改成 `False` |
| 改了 `config.py`，遊戲卻沒變 | kernel 還在用舊的程式 | 「Kernel」→「Restart Kernel」，再從頭執行 |
| 玩的時候頭暈 | 畫面捲動 | `config.py` 的 `grass_scrolls` 保持 `False`；可以把 `start_speed` 調低 |

## 九、修改教材

- **改遊戲手感**（重力、速度、障礙物大小、顏色）：只改 `config.py`，每個數值都有說明。
- **改了任何 `.py` 檔之後，要重新啟動 kernel**（「Kernel」→「Restart Kernel」，VS Code 是上方的「Restart」）。`import engine` 在同一個 kernel 裡只會真正載入一次，之後再執行也不會重新讀檔，所以沒重啟的話，遊戲還是用舊的程式。上課中途改了 `config.py`，也要請學生重啟。
- **改 notebook 內容**：只改 `solution.ipynb`，再執行 `python make_game_notebook.py` 重新產生 `game.ipynb`。不要直接改 `game.ipynb`，下次產生時會被蓋掉。
- **改錯誤訊息的用語**：全部在 `checks.py`。改完記得同步更新本手冊的「錯誤訊息一覽」。
- **換一套官方關卡**：改 `config.py` 的 `official_seed`。比賽進行中絕對不要改，否則前後的分數不能比較。
- **換圖片和音效**：見 `assets/README.md`。
- **交給學生之前**：執行 `python clear_outputs.py`。
