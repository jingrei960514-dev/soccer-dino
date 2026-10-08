# 足球小恐龍

一款教學用的 pygame 小遊戲，玩法類似 Chrome 的小恐龍：球員帶球自動往前跑，按空白鍵跳過三角錐、鏟球的防守球員，躲開飛過來的球鞋，一路衝進球門。

這是大學服務學習的教材，對象是剛學過 Python 變數、if、迴圈、清單的國中生，一堂課一小時。學生拿到的是一個**壞掉的遊戲**，要自己把它修好、改成自己的版本，最後用官方版本比分數。

## 課堂流程

1. **試玩壞掉的版本**：跳不起來、撞到沒事、障礙物都一樣、畫面不會加速。
2. **逐項修好**：由上到下有四個問題，第一個改關卡清單，其他三個是填空，把 `______` 換成正確的程式。
3. **改成自己的版本**：名字、球衣顏色、背號、關卡都可以改；做得快的同學挑戰二段跳和射門。
4. **同學互玩**。
5. **官方比賽**：大家玩同一個固定的關卡，助教用計分板登記分數。

學生只在 notebook 裡寫很短的程式，遊戲迴圈、畫面、碰撞都由引擎處理。修好之後，學生的程式長這樣：

```python
# ===== 我的關卡 =====
course = ['cone', 'gap', 'defender', 'ball', 'shoe']

# ===== 遊戲規則 =====
jump_power = 12

# 按下跳躍鍵時會執行這裡
def on_jump_key(game):
	if game.on_ground:
		game.vy = -jump_power

# 撞到障礙時會執行這裡
def on_hit(game):
	game.lives = game.lives - 1
	if game.lives == 0:
		game.over()

# 每過一秒會執行這裡
def on_tick(game):
	game.speed = game.speed + 0.2

engine.run(globals())
```

## 快速開始

需要 Python 3 和 pygame（開發時用的是 Python 3.10、pygame 2.6）。

```
python -m pip install pygame jupyterlab
```

**用 Jupyter（上課的方式）**：打開 `game.ipynb`，從上到下每一格按 `Shift + Enter` 執行，最後一格會跳出遊戲視窗。

**用終端機（開發測試用）**：

```
python run.py                    執行 solution.ipynb（全部修好的版本）
python run.py game.ipynb         執行壞掉的版本
python run.py official.ipynb     執行官方比賽版本
```

## 操作方式

| 按鍵 | 功能 |
| --- | --- |
| 空白鍵、上方向鍵、W | 跳躍 |
| F、X | 射門（挑戰題） |
| R、Enter | 重新開始 |
| Esc | 關閉視窗 |

## 檔案

| 檔案 | 用途 |
| --- | --- |
| `game.ipynb` | 學生拿到的壞掉版本，由 `make_game_notebook.py` 產生 |
| `solution.ipynb` | 全部修好的教師版 |
| `official.ipynb` | 官方比賽用，只能改球員設定 |
| `scoreboard.html` | 比賽計分板，單一檔案、不需網路，用瀏覽器打開後投影 |
| `engine.py` | 遊戲規則與主迴圈 |
| `config.py` | 所有可以調整的數值：速度、重力、大小、顏色、按鍵 |
| `drawing.py` | 畫面 |
| `sound.py` | 音效 |
| `checks.py` | 防呆檢查與中文錯誤訊息 |
| `assets/` | 選用的圖片和音效，說明在 `assets/README.md` |
| `run.py` | 不開 Jupyter，直接執行 notebook |
| `make_game_notebook.py` | 從 `solution.ipynb` 產生 `game.ipynb` |
| `clear_outputs.py` | 清除 notebook 的執行結果 |
| `TEACHER_GUIDE.md` | 教師手冊 |
| `ARCHITECTURE.md` | 程式架構說明 |

## 文件

- **上課的老師和助教**：請看 [`TEACHER_GUIDE.md`](TEACHER_GUIDE.md)。內容有課前準備、Jupyter 設定、參考答案、挑戰題提示卡、所有錯誤訊息的原因，以及常見問題。
- **要修改程式的人**：請看 [`ARCHITECTURE.md`](ARCHITECTURE.md)。內容有整體架構、每一幀的流程、每個檔案負責什麼。

## 特色

- **防呆**：遊戲開始前會檢查學生的設定，打錯字時提示最像的正確名稱。學生的函式出錯時，會先關掉視窗，再用繁體中文說明哪個函式、哪一行出錯，以及可能的原因。
- **官方模式**：無盡關卡、持續加速。關卡用固定的亂數種子產生，每個人遇到的完全一樣，分數才能互相比較。
- **可以重複執行**：在同一個 Jupyter kernel 裡重複執行、中途出錯、按中斷，都能馬上再玩一次。
- **換素材不用改程式**：把圖檔或音效檔放進 `assets/` 就會自動使用，沒放也能玩。
- **減少頭暈**：背景和看台不捲動，只有腳下的小草跟著動。

## 修改教材

| 想做的事 | 做法 |
| --- | --- |
| 改遊戲手感 | 只改 `config.py` |
| 改 notebook 內容 | 改 `solution.ipynb`，再執行 `python make_game_notebook.py` 重新產生 `game.ipynb` |
| 改錯誤訊息的用語 | 改 `checks.py`，並同步更新 `TEACHER_GUIDE.md` |
| 換一套官方關卡 | 改 `config.py` 的 `official_seed` |
| 交給學生之前 | 執行 `python clear_outputs.py` |

## 程式碼規範

這份程式會改寫成教材，所以刻意用最直白的寫法，不用進階語法和設計模式。所有 `.py`、`.ipynb` 和文件都遵守：

- 縮排一律使用一個 tab。
- 變數與函式名稱使用 snake_case。
- 字串一律使用單引號。
- 條件式不加括號；二元運算子左右各一個空格；逗號後面一個空格。
- 註解寫在該行程式的上一行，用繁體中文說明「為什麼」。
- 中文使用全形標點；中文與英文、數字之間加一個空格。

## 素材與版權

遊戲裡的人物、球場、聲音都是程式即時畫出、產生的，沒有使用任何外部素材，也沒有出現真實人物。在 `assets/` 加入素材時，只能用自己製作或授權允許自由使用的檔案。
