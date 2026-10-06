# 足球小恐龍：程式架構

這份文件說明整個遊戲怎麼組成、每一幀發生什麼事，以及每個檔案負責什麼。每完成一個開發階段就會更新。

目前進度：七個階段全部完成。

## 核心想法：引擎呼叫學生的函式

學生只寫「變數」和「幾個短函式」，不寫主迴圈。真正的遊戲迴圈在 `engine.py` 裡，它會在適當的時機呼叫學生的函式：

| 時機 | 引擎呼叫的函式 | 學生通常在裡面做什麼 |
| --- | --- | --- |
| 按下跳躍鍵 | `on_jump_key(game)` | 在地上時把 `game.vy` 設成負數 |
| 撞到障礙物 | `on_hit(game)` | `game.lives` 減一，歸零時呼叫 `game.over()` |
| 每過一秒 | `on_tick(game)` | `game.speed` 加一點 |
| 按下射門鍵（F 或 X） | `on_shoot_key(game)` | 有彈藥才呼叫 `game.shoot()`，射完彈藥減一 |

學生的程式最後只有一行 `engine.run(globals())`。`globals()` 是一個字典，裡面有學生定義的所有變數與函式，引擎從裡面讀取 `player_name`、`course`、`on_jump_key` 等等。學生沒有定義的項目會用 `config.py` 的預設值；沒有定義的函式則當作「什麼都不做」，所以不會報錯。

## 檔案用途

| 檔案 | 用途 |
| --- | --- |
| `config.py` | 所有可以調整的數值：視窗大小、重力、速度上下限、障礙物大小、顏色、按鍵。想改手感只改這裡。 |
| `engine.py` | 遊戲規則與狀態：`Game` 類別、讀取學生設定、主迴圈、跳躍物理、碰撞、過關判斷。 |
| `checks.py` | 防呆：遊戲開始前檢查學生的設定，遊戲中把學生函式的錯誤翻譯成中文說明。所有給學生看的錯誤訊息都在這裡。 |
| `drawing.py` | 所有畫圖的程式。每種角色一個 `draw_` 函式，先找 `assets/` 裡的圖檔，找不到才用幾何圖形。 |
| `sound.py` | 音效：載入 `assets/` 裡的音效檔，找不到就用程式產生嗶聲；沒有喇叭時自動靜音。 |
| `assets/` | 放圖片和音效的資料夾，檔名與大小寫在裡面的 `README.md`。空的也能玩。 |
| `run.py` | 開發用的入口，讀出 notebook 裡的程式格直接執行，不用開 Jupyter。`python run.py` 執行 solution.ipynb，`python run.py game.ipynb` 執行其他 notebook。 |
| `solution.ipynb` | 教師版 notebook，全部問題都已修好。也是破壞版的來源。 |
| `game.ipynb` | 學生拿到的破壞版，由 `make_game_notebook.py` 產生，**不要直接修改**。 |
| `official.ipynb` | 官方比賽用的 notebook，只設定球員，最後一格呼叫 `engine.run_official(globals())`。 |
| `make_game_notebook.py` | 從 solution.ipynb 產生 game.ipynb：找出特定的格子換成破壞版內容，並清除執行結果。 |
| `clear_outputs.py` | 清除 notebook 的執行結果，交給學生之前執行。 |
| `scoreboard.html` | 官方比賽的計分板，單一檔案、不需網路，用瀏覽器打開後投影。 |
| `TEACHER_GUIDE.md` | 教師手冊：課前準備、參考答案、提示卡、所有錯誤訊息、常見問題。 |

## notebook 怎麼被執行

學生的 notebook 依序是：`import engine` → 球員設定 → 關卡 → 三個規則函式（各一格）→ `engine.run(globals())`。每個要修的函式各自一格，上課時可以一格一格修。

有兩種執行方式，結果完全相同：

- **Jupyter**：學生一格一格執行，最後一格把 notebook 的 `globals()` 交給引擎。
- **`run.py`**：把 notebook 的所有程式格接成一段程式碼，用 `exec` 放在一個空字典裡執行。這個字典就是那段程式的 `globals()`，所以最後一行 `engine.run(globals())` 一樣能拿到所有變數和函式。

Jupyter 有一個要注意的地方：kernel 會記住所有執行過的東西。學生如果刪掉某個函式的格子，舊的函式還留在 kernel 裡，遊戲照樣會用它；要真正清掉必須「重新啟動 kernel」。

## 破壞版怎麼產生

`make_game_notebook.py` 讀取 solution.ipynb，用「格子裡含有的文字」找出要換的格子，整格換成腳本裡寫好的破壞版內容：

| 找的文字 | 換成 |
| --- | --- |
| `教師版` | 學生版的開頭說明，告訴學生有【問題一】到【問題四】 |
| `# ===== 我的關卡 =====` | 【問題三】全部都是 `'cone'` 的清單 |
| `def on_jump_key` | 【問題一】只有提示註解和 `pass` |
| `def on_hit` | 【問題二】只有提示註解和 `pass` |
| `def on_tick` | 【問題四】只有提示註解和 `pass` |

只要有一項找不到，腳本就不會寫檔，避免產生一份「少壞一項」的破壞版卻沒人發現。修改教材的流程：改 solution.ipynb → 執行 `python make_game_notebook.py`。

## `game` 物件有哪些屬性

學生會用到的：

| 屬性 | 意義 |
| --- | --- |
| `game.on_ground` | 球員是否站在地上 |
| `game.vy` | 垂直速度，負數往上、正數往下 |
| `game.lives` | 剩幾條命 |
| `game.speed` | 畫面每一幀捲動幾像素 |
| `game.jump_count` | 已經跳了幾次，落地時引擎自動歸零 |
| `game.ammo` | 射門的彈藥數 |
| `game.over()` | 讓遊戲結束 |
| `game.shoot()` | 射出一顆貼地的球，碰到防守球員就把他踢飛 |

引擎自己用的：`mode`、`shots`（射出去的球）、`sounds_to_play`（這一幀要播的音效）、`known_attributes`（抓打錯字用）、`defenders_kicked`、`player_y`（球員腳底高度）、`camera_x`（畫面捲了多遠）、`things`（關卡元素清單）、`goal_x`、`invincible_timer`、`tick_timer`、`frame_count`、`is_over`、`result`、`progress`。

## 座標怎麼算

- 每個關卡元素都有一個「世界座標」`x`，代表它在整條跑道上的位置。
- `camera_x` 代表畫面已經往右捲了多遠。
- 畫在螢幕上的位置 = 世界座標 - `camera_x`。
- 球員永遠畫在螢幕的 `config.player_x`，所以他在世界中的位置是 `camera_x + player_x`。
- 螢幕的 y 座標往下增加，所以往上跳要把 `vy` 設成負數。

## 關卡怎麼產生

`build_course()` 依序讀學生的 `course` 清單，每個名稱佔一格（寬 `config.slot_width`）。`'gap'` 只佔位置、不放東西；其他名稱會變成一個字典：

```python
{'kind': 'cone', 'x': 1300, 'done': False, 'kicked': False, 'lift': 0}
```

`done` 代表已經撞過或撿過，之後不會再觸發；`kicked` 和 `lift` 是防守球員被踢飛時用的（是否被踢飛、離地多高）。清單結束後再往後 `goal_distance_after_course` 就是球門。

## 兩種模式

| | 學生模式 | 官方模式 |
| --- | --- | --- |
| 啟動 | `engine.run(globals())` | `engine.run_official(globals())` |
| 讀取設定 | `read_student_settings()` | `read_official_settings()` |
| 規則函式 | 學生寫的 `on_jump_key` 等 | 引擎內建的 `official_on_jump_key` 等 |
| 關卡 | 開始時 `build_course()` 一次產生 | 每一幀 `extend_official_course()` 往前補 |
| 結束 | 抵達球門，或學生呼叫 `game.over()` | 命用完 |
| 畫面 | 有球門、有進度條 | 顯示「官方版本」，結束畫面用大字 |

兩種模式共用 `read_player_settings()`（名字、球衣、背號）和 `start_game()`（開視窗、主迴圈、關視窗）。官方模式把內建函式放進 `settings` 裡學生函式的位置，所以主迴圈完全不用分辨現在是哪一種模式。

### 官方關卡怎麼保證每個人都一樣

- 每一局建立一個 `random.Random(config.official_seed)`，只給關卡用。學生程式裡用 `random` 不會影響它。
- 每一格只呼叫一次 `random()`，再自己換算成要放什麼。不用 `random.choice()`，因為不同 Python 版本的算法可能不同。
- 難度（空白的機率）和格子寬度都只跟「第幾格」有關，跟時間、玩家表現無關。

### 官方關卡怎麼保證公平

- 跳過障礙物後的 `official_high_ball_safe_slots` 格內不放高空球，免得球員還在空中就被打到。
- 格子寬度隨格子編號從 340 慢慢加寬到 840。速度變快後，跳一次會在空中跑得更遠；格子不變寬的話，連續兩個障礙物會躲不掉。

## 程式執行流程

```
engine.run(globals())               engine.run_official(globals())
	can_start()                        can_start()                    有沒有 pygame、最後一格有沒有寫對
	checks.check_student_settings()    checks.check_player_settings() 有問題就印出來，不開視窗
	read_student_settings()            read_official_settings()
	start_game()                       兩種模式從這裡開始共用
	sound.prepare_mixer()        混音器的設定必須在 pygame.init() 之前
	pygame.init()
	drawing.load_images()        每次開始都重新載入圖片和音效，換了 assets 不用重啟 kernel
	sound.load_sounds()
	while keep_playing:
		play_one_round()         玩一局，按 R 或 Enter 會回傳 True 再玩一局
	pygame.quit()                放在 finally 裡，出錯也一定會關視窗
	print(message)               學生的函式出錯時，視窗關掉之後才印出中文說明
```

## 主迴圈每一幀的流程

`play_one_round()` 裡的 `while True` 每跑一圈就是一幀（每秒 60 幀）：

1. `handle_events()`：讀鍵盤與關閉視窗。按跳躍鍵就呼叫學生的 `on_jump_key`，按射門鍵就呼叫 `on_shoot_key`；按 Esc 或關閉視窗就結束；按 R 或 Enter 重新開始。
2. 如果遊戲還沒結束，`update_game()` 依序做（官方模式會用內建規則取代學生函式）：
	1. 計時，每滿一秒呼叫學生的 `on_tick`。
	2. 用 `keep_in_range()` 把 `speed`、`vy` 拉回合理範圍，防止學生設的極端數值讓遊戲壞掉。
	3. `update_player()`：`vy` 加上重力，位置加上 `vy`；碰到地面就停住、`on_ground` 設成 True、`jump_count` 歸零。
	4. `camera_x` 加上 `speed`，畫面往前捲；官方模式用 `extend_official_course()` 在前方補上新的格子；`move_things()` 讓防守球員和高空球再多往左移，被踢飛的防守球員往右上飛走，並刪掉已經離開畫面的東西。
	5. `move_shots()`：射出去的球往前飛，碰到防守球員就把他踢飛，球也消失。
	6. `check_collisions()`：撿到球就加分加彈藥；撞到障礙物且不在無敵時間，就先設定無敵，再呼叫學生的 `on_hit`。
	7. 無敵時間倒數。
	8. 計算分數（跑的距離 + 撿到的球 + 踢飛的防守球員）。
	9. 學生模式才有：計算進度，球員碰到球門就過關。
3. `sound.play_sounds()`：播放這一幀放進 `game.sounds_to_play` 的音效，播完清空。
4. `drawing.draw_frame()`：由遠到近畫背景、球門、關卡元素、球員、上方資訊；遊戲結束時再蓋上結束畫面。
5. `pygame.display.flip()` 把畫好的畫面顯示出來，`clock.tick()` 等待到下一幀。

## 圖片和音效怎麼運作

### 圖片

- `drawing.load_images()` 在開好視窗後，讀取 `config.image_files` 裡每一個檔案，縮放成 `config.image_sizes` 的大小，放進 `images` 字典。找不到或讀不出來的就不放。
- 每個 `draw_` 函式先看 `images` 裡有沒有自己的圖：有就用 `draw_image()` 貼上，沒有就用原本的幾何圖形。
- `draw_image()` 用「左下角」對齊，因為遊戲裡的東西幾乎都站在地上，用底部算位置最直覺。
- 障礙物的圖片大小直接取自碰撞框的數值（例如 `cone_width`），所以圖片和碰撞判定一定對得起來。
- 背景圖不捲動，只有腳下的小草會動，避免頭暈。

### 音效

- 規則的部分（`engine.py`）不直接播放聲音，只把名稱放進 `game.sounds_to_play`，例如撞到時放 `'hit'`。主迴圈每一幀統一播放後清空。這樣規則和聲音分開，沒有喇叭的電腦也不用改任何規則。
- 跳躍的規則是學生寫的，引擎不知道他有沒有真的讓球員跳起來，所以比較呼叫 `on_jump_key` 前後的 `vy`：變得更往上才播放跳躍聲。
- `sound.load_sounds()` 先找 `assets/` 裡的音效檔；找不到就用 `make_beep()` 依照 `config.beep_notes` 產生嗶聲。混音器開不起來（沒有音效卡）時回傳空字典，播放時查不到就跳過，等於靜音。

## 延伸功能怎麼運作

- **二段跳**：引擎每一幀在球員落地時把 `game.jump_count` 歸零，其他全部交給學生的 `on_jump_key`：「`jump_count` 小於 2 才能跳，跳了就加一」。引擎不需要知道學生有沒有做二段跳。
- **射門**：`game.shoot()` 只負責射出球，不檢查彈藥，因為「有彈藥才能射、射完減一」是學生要寫的規則。畫面上同時最多 `max_shots_on_screen` 顆球，避免學生忘了扣彈藥又狂按，讓遊戲變慢。球一律貼地，只對防守球員有效，碰到其他東西直接穿過。
- 官方模式的 `official_on_jump_key` 和 `official_on_shoot_key` 就是這兩項的參考答案。
- notebook 裡的「挑戰題」說明格和一個空的程式格放在 solution.ipynb，`make_game_notebook.py` 會原封不動帶到 game.ipynb。

## 防呆怎麼運作

使用者是初學的國中生，所以錯誤分成三個時間點處理，每一則訊息都盡量說清楚「哪裡錯、可能的原因、怎麼改」。

### 1. 遊戲開始前（不開視窗，直接列出所有問題）

`checks.check_student_settings()` 一次找出所有問題，學生不用改一個、執行一次，才看到下一個：

| 檢查 | 例子 |
| --- | --- |
| 名字、背號的型別與長度 | `player_name = ''`、`jersey_number = 10.5` |
| 顏色名稱，打錯時提示最像的 | `'Red'` → 是不是要寫 `'red'`？ |
| `course` 是清單、不是空的、不超過 `max_course_length` | `course = 'cone'` |
| `course` 裡每個名稱，打錯時提示最像的 | `'defnder'` → 是不是要寫 `'defender'`？ |
| 規則函式真的是函式，而且括號裡剛好有一個 `game` | `def on_hit():` |

另外 `find_misspelled_functions()` 會找出名字很像但不完全一樣的函式（例如 `on_jump`）。這只是提醒，遊戲照常開始，因為 Jupyter 會記住改名之前的舊函式，擋下來的話學生改好了還是開不了遊戲。

「最像的名字」用 Python 內建的 `difflib.get_close_matches()` 找。

### 2. 遊戲中，學生的函式出錯

所有學生函式都經過 `call_student_function()`：

1. 用 `try` 呼叫學生的函式。出錯的話，`checks.explain_error()` 寫好中文說明，包成 `StudentCodeError` 丟出去。
2. `start_game()` 接到 `StudentCodeError` 後，`finally` 先關掉視窗，再印出說明。
3. 說明包含：哪個函式、出錯的那一行、可能的原因、原始的英文訊息（給助教看）。原因依錯誤種類判斷（`NameError`、`AttributeError`、`TypeError` 等），只寫初學者最常遇到的情況。

「出錯的那一行」是從錯誤的追蹤紀錄裡，找和學生函式在同一格的最後一層。Jupyter 會自動記住每一格的程式碼；`run.py` 則要自己把程式碼放進 `linecache`，才查得到那一行。

只接住 `StudentCodeError`，是為了讓引擎自己的 bug 照常顯示 traceback，開發時才找得到。

### 3. 學生的函式沒出錯，但把 `game` 改壞了

有些錯誤當下不會發生，要等引擎拿數值計算時才出錯，那時訊息會指向 engine.py，學生看不懂。所以每次學生函式執行完，`checks.check_game_values()` 會馬上檢查：

- `vy`、`lives`、`speed`、`jump_count`、`ammo` 必須是數字，例如 `game.speed = 'fast'` 會被擋下。
- 屬性名稱打錯，例如 `game.live = game.lives - 1`。Python 不會報錯，只會多出一個 `live` 屬性，命永遠不會變少。`Game` 建立時把原本的屬性記在 `known_attributes`，多出來而且和內建名稱很像的就擋下。學生自己取的、不像內建名稱的屬性（例如 `game.my_counter`）不擋，留給學生發揮創意。
- `game.over = True` 這種把函式當成變數的寫法。

數值太極端（跳躍力 99999、速度 10 億）不算錯誤，`keep_in_range()` 會把它們拉回合理範圍。

### Jupyter 的穩定性

- 找不到 pygame 時，`import engine` 不會出錯，執行最後一格時才印出中文說明，並告訴助教這個 kernel 用的是哪個 Python。
- 在 Jupyter 按「中斷」時，接住 `KeyboardInterrupt`，關掉視窗並印出一句說明，不顯示 traceback。
- 不管怎麼結束（正常、出錯、中斷），`pygame.quit()` 都在 `finally` 裡，同一個 kernel 可以馬上再執行一次。

## 為什麼這樣設計

- **所有學生函式都經過 `call_student_function()`**：錯誤處理和數值檢查只需要寫在這一個地方。
- **錯誤訊息全部放在 `checks.py`**：之後要修改用語，或把訊息整理進教師文件，只要看這一個檔案。
- **`game.over()` 只做記號**：真正停止由主迴圈處理，學生函式執行到一半時遊戲狀態不會被清空。
- **先設無敵再呼叫 `on_hit`**：同一幀撞到兩個障礙物時不會連扣兩條命。
- **不呼叫 `sys.exit()`**：在 Jupyter 裡會把 kernel 一起關掉，所以只用 `pygame.quit()` 關視窗。
