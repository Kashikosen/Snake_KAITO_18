#描画ファイル名 Snake_KAITO.pyxres
#呼び出す時は、 pyxel edit Snake_KAITO.pyxres
#https://kitao.github.io/pyxel/wasm/launcher/?run=Kashikosen.Snake_KAITO_18.Snake_KAITO

from cmath import pi
import math
import random
import pyxel
import time
import enum
import webbrowser
import collections




#方向ラベル
class Direction(enum.Enum):
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3



#状態遷移
class GameState(enum.Enum):
    GAME_TITLE = 0
    RUNNING = 1
    GAME_OVER = 2



#レベル(壁作成)
class Level:
    def __init__(self):
        self.tm = 0
        self.u = 0
        self.v = 0
        self.w = 320
        self.h = 272
    
    def draw(self):
       pyxel.bltm(0, 0, self.tm, self.u, self.v, self.w, self.h)



class Ice:
    def __init__(self, x, y, flavor_x, flavor_y):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 16
        self.flavor_x = flavor_x
        self.flavor_y = flavor_y
    
    def draw(self):
        pyxel.blt(self.x, self.y, 0, self.flavor_x, self.flavor_y, self.w, self.h)
    
    def intersects(self, u, v, w, h):
            is_intersected = False
            if(
                u + w > self.x
                and self.x + self.w > u
                and v + h > self.y
                and self.y + self.h > v
            ):
                is_intersected = True
            return is_intersected
    
    def move(self, new_x, new_y):
        self.x = new_x
        self.y = new_y
    
    def flavor(self, new_flavor_x, new_flavor_y):
        self.flavor_x = new_flavor_x
        self.flavor_y = new_flavor_y



#体の向きを含む描画
#何かが交差するかのチェック
class Kaito:
    def __init__(self, x, y, is_body=False):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 16
        self.is_body = is_body
    
    def draw(self, direction):
        width = self.w
        height = self.h
        sprite_x = 0
        sprite_y = 16

        if self.is_body:
            if direction == Direction.RIGHT:
                sprite_x = 48
                sprite_y = 0
            if direction == Direction.LEFT:
                sprite_x = 32
                sprite_y = 0
            if direction == Direction.DOWN:
                sprite_x = 0
                sprite_y = 0
            if direction == Direction.UP:
                sprite_x = 16
                sprite_y = 0
        pyxel.blt(self.x, self.y, 0, sprite_x, sprite_y, width, height)
    
    def intersects(self, u, v, w, h):
        is_intersected = False
        if(
            u + w > self.x
            and self.x + self.w > u
            and v + h > self.y
            and self.y + self.h > v
        ):
            is_intersected = True
        return is_intersected



def center_text(self, text, page_width, char_width=pyxel.FONT_WIDTH):
    text_width = len(text) * char_width
    return (page_width - text_width) / 2

def right_text(text, page_width, char_width=pyxel.FONT_WIDTH):
    text_width = len(text) * char_width
    return page_width - (text_width + char_width)


#テキスト・スコア処理
class Hud:
    def __init__(self):
        self.title_text = "SCORE : "
        self.title_text_x = 4
        self.score_text = str(0)
        self.score_text_x = right_text(self.score_text, 196)
        self.level_text = "Level 0"
        self.level_text_x = 10
        self.ice_text = "Ices"
        self.ice_text_x = len(self.level_text) * pyxel.FONT_WIDTH + self.level_text_x + 5
    
    def draw_title(self):
        #pyxel.rect(self.title_text_x -16 , 0, len(self.title_text) * pyxel.FONT_WIDTH + self.level_text_x + 16, 16, 7)
        pyxel.text(self.title_text_x, 6, self.title_text, 7)
    
    def draw_score(self, score):
        self.score_text = str(score)
        self.score_text_x = 48
        #pyxel.rect(self.score_text_x - 16, 0, len(self.score_text) * pyxel.FONT_WIDTH + 16, pyxel.FONT_HEIGHT + 8, 7)
        pyxel.text(self.score_text_x, 6, self.score_text, 7)
    



class App:
    def __init__(self):  #初期化
        pyxel.init(320, 272, title="KAITO18th", fps=60)
        pyxel.load("Snake_KAITO.pyxres")
        pyxel.mouse(True)

        self.current_game_state = GameState.GAME_TITLE
        self.level = Level()
        self.hud = Hud()
        self.ice = Ice(128,96, 0, 16)
        self.kaito = []
        self.kaito.append(Kaito(48,32, is_body=True))
        self.kaito_direction: Direction = Direction.RIGHT
        self.sections_to_add = 0
        self.speed = 8
        self.time_last_frame = time.time()
        self.dt = 0
        self.time_since_last_move = 0
        self.score = 0
        self.ices_eaten_total = 0
        self.input_queue = collections.deque()  #方向転換の記憶
        self.play_music = True
        if self.play_music:
            pyxel.playm(0, loop=True)
        pyxel.run(self.update, self.draw)  #アプリケーションの実行
    
    def start_new_game(self):
        self.current_game_state = GameState.RUNNING
        self.kaito.clear()
        #再実行
        self.kaito.append(Kaito(48,32, is_body=True))
        self.kaito_direction: Direction = Direction.RIGHT
        self.sections_to_add = 0
        self.speed = 8
        self.time_last_frame = time.time()
        self.dt = 0
        self.time_since_last_move = 0 
        self.score = 0
        self.ices_eaten_total = 0
        self.input_queue.clear()
        self.move_ice()
        if self.play_music:
            pyxel.playm(0, loop=True)
    
    def update(self):  #フレームの更新処理
        time_this_frame = time.time()
        self.dt = time_this_frame - self.time_last_frame
        self.time_last_frame = time_this_frame
        self.time_since_last_move += self.dt
        self.check_input()
        if self.current_game_state == GameState.RUNNING:
            if self.time_since_last_move >= 1 / self.speed:
                self.time_since_last_move = 0
                self.move_kaito()
                self.check_collisions()
                self.score = self.ices_eaten_total

        if pyxel.btn(pyxel.KEY_Q):
            pyxel.quit()
        

    def toggle_music(self):
        if self.play_music:
            self.play_music = False
            pyxel.stop()
        else:
            self.play_music = True
            pyxel.playm(0, loop=True)
    
    def draw_running(self):  #描画処理
        pyxel.cls(0)
        self.level.draw()
        self.ice.draw()
        for s in self.kaito:
            s.draw(self.kaito_direction)
        self.hud.draw_title()
        self.hud.draw_score(self.score)
        #pyxel.text(10, 224, str(self.current_game_state), 12)
        #音楽再生かどうか
        if self.play_music == False:
            pyxel.blt(306, 0, 0, 0, 208, 16, 16)
        else:
            pyxel.blt(306, 0, 0, 16, 208, 16, 16)

    
    def check_collisions(self):  #衝突判定
        #アイス
        if self.ice.intersects(self.kaito[0].x, self.kaito[0].y, self.kaito[0].w, self.kaito[0].h):
            pyxel.play(0,0)
            self.speed += (self.speed * 0.1)
            self.sections_to_add += 1
            self.move_ice()
            self.ices_eaten_total += 1
        #マフラー
        for s in self.kaito:
            if s == self.kaito[0]:
                continue
            if s.intersects(self.kaito[0].x, self.kaito[0].y, self.kaito[0].w, self.kaito[0].h):
                pyxel.stop()
                pyxel.play(0, 2)
                self.current_game_state = GameState.GAME_OVER
        #壁
        if self.kaito[0].x < 16 or self.kaito[0].x > 303 or self.kaito[0].y < 32 or self.kaito[0].y > 255:
            pyxel.stop()
            pyxel.play(0, 2)
            self.current_game_state = GameState.GAME_OVER
    
    def move_ice(self):
        #アイスのランダム配置
        #壁の中や蛇以外で配置
        good_position = False
        while not good_position:
            new_x = random.randrange(16, 304, 16)
            new_y = random.randrange(32, 256, 16)
            good_position = True
            #KAITOチェック
            for s in self.kaito:
                if(
                    new_x + 16 > s.x
                    and s.x + s.w > new_x
                    and new_y + 16 > s.y
                    and s.y + s.w > new_y
                ):
                    good_position = False
                    break
            #アイス移動
            if good_position:
                self.ice.move(new_x, new_y)
    
    ###没
    def flavor_ice(self):
        #アイスの種類をランダムに
        good_flavor = False
        while not good_flavor:
            ice_flavor = random.randrange(0, 9, 1)
            print(ice_flavor)
            good_flavor = True
        if ice_flavor > 5:
            new_flavor_x = 16
            new_flavor_y = 16
        else:
            new_flavor_x = 0
            new_flavor_y = 16
        if good_flavor:
            self.ice.flavor(new_flavor_x, new_flavor_y)
    ###

    def move_kaito(self):
        #方向転換の必要があるか？
        if len(self.input_queue):
            self.kaito_direction = self.input_queue.popleft()
        #マフラーの伸び
        if self.sections_to_add > 0:
            self.kaito.append(Kaito(self.kaito[-1].x, self.kaito[-1].y))
            self.sections_to_add -= 1
        #体の向きを変える
        previous_location_x = self.kaito[0].x
        previous_location_y = self.kaito[0].y
        if self.kaito_direction == Direction.RIGHT:
            self.kaito[0].x += self.kaito[0].w
        if self.kaito_direction == Direction.LEFT:
            self.kaito[0].x -= self.kaito[0].w
        if self.kaito_direction == Direction.DOWN:
            self.kaito[0].y += self.kaito[0].w
        if self.kaito_direction == Direction.UP:
            self.kaito[0].y -= self.kaito[0].w       
        #マフラーの向きを変える
        for s in self.kaito:
            if s == self.kaito[0]:
                continue
            current_location_x = s.x
            current_location_y = s.y
            s.x = previous_location_x
            s.y = previous_location_y
            previous_location_x = current_location_x
            previous_location_y = current_location_y
    
    def check_input(self):
        if pyxel.btnp(pyxel.KEY_M) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (306 <= pyxel.mouse_x <= 322) and (0 <= pyxel.mouse_y <= 16)):
            self.toggle_music()
        if pyxel.btn(pyxel.KEY_RIGHT):
            if len(self.input_queue) == 0:
                if self.kaito_direction != Direction.LEFT and self.kaito_direction != Direction.RIGHT:
                    self.input_queue.append(Direction.RIGHT)
            else:
                if self.input_queue[-1] != Direction.LEFT and self.input_queue[-1] != Direction.RIGHT:
                    self.input_queue.append(Direction.RIGHT)
        elif pyxel.btn(pyxel.KEY_LEFT):
            if len(self.input_queue) == 0:
                if self.kaito_direction != Direction.RIGHT and self.kaito_direction != Direction.LEFT:
                    self.input_queue.append(Direction.LEFT)
            else:
                if self.input_queue[-1] != Direction.RIGHT and self.input_queue[-1] != Direction.LEFT:
                    self.input_queue.append(Direction.LEFT)
        elif pyxel.btn(pyxel.KEY_DOWN):
            if len(self.input_queue) == 0:
                if self.kaito_direction != Direction.UP and self.kaito_direction != Direction.DOWN:
                    self.input_queue.append(Direction.DOWN)
            else:
                if self.input_queue[-1] != Direction.UP and self.input_queue[-1] != Direction.DOWN:
                    self.input_queue.append(Direction.DOWN)
        elif pyxel.btn(pyxel.KEY_UP):
            if len(self.input_queue) == 0:
                if self.kaito_direction != Direction.DOWN and self.kaito_direction != Direction.UP:
                    self.input_queue.append(Direction.UP)
            else:
                if self.input_queue[-1] != Direction.DOWN and self.input_queue[-1] != Direction.UP:
                    self.input_queue.append(Direction.UP)
    
    #タイトル画面
    def draw_game_title(self):
        self.current_game_state == GameState.GAME_TITLE
        pyxel.bltm(0, 0, 0, 0, 320, 320, 272)
        pyxel.text(8, 8, "# KAITO18th", 7)
        pyxel.text(112, 192, "> Press ENTER to Start", 7)
        pyxel.text(44, 248, "This work depicts the character ""KAITO"" of Crypton Future Media, Inc.", 6)
        pyxel.text(40, 256, " under the PeerPro Character License." , 6)

        #ENTERでゲーム画面に遷移
        if pyxel.btnp(pyxel.KEY_RETURN) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (104 <= pyxel.mouse_x <= 208) and (184 < pyxel.mouse_y < 204)):
            self.current_game_state = GameState.RUNNING
            pyxel.play(0,1)
        
        #Twitterリンク
        pyxel.blt(264, 224, 0, 32, 64, 16, 16, 0)
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (264 <= pyxel.mouse_x <= 280) and (224 <= pyxel.mouse_y <= 240):
            webbrowser.open("https://twitter.com/kasikosen830")
        
        #GitHubリンク
        pyxel.blt(288, 224, 0, 48, 64, 16, 16, 0)
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (288 <= pyxel.mouse_x <= 304) and (224 <= pyxel.mouse_y <= 240):
            print("GitHub")
            webbrowser.open("https://github.com/Kashikosen/Snake_KAITO_18")
    
    #ゲームオーバー画面
    def draw_game_over(self):
        pyxel.bltm(32, 48, 0, 0, 640, 256, 192)
        #結果の表示
        pyxel.text(96, 136, "SCORE : ", 1)
        pyxel.text(168, 136, str(self.score), 1)
        #リトライ
        pyxel.text(128, 176, "> Press R to Retry", 8)
        if pyxel.btn(pyxel.KEY_R) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (120 <= pyxel.mouse_x <= 208) and (172 <= pyxel.mouse_y <= 180)):
            pyxel.play(0,1)
            self.start_new_game()
        #やめる
        pyxel.text(96, 188, "> Press Esc or Q to Exit the Game", 5)
        if pyxel.btn(pyxel.KEY_Q) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (88 <= pyxel.mouse_x <= 224) and (184 <= pyxel.mouse_y <= 192)):
            pyxel.quit()
        #Twitterに結果をアップ
        pyxel.text(176, 214, "Post your results?", 5)
        pyxel.blt(256, 208, 0, 32, 64, 16, 16, 0)
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and (256 <= pyxel.mouse_x <= 272) and (208 <= pyxel.mouse_y <= 224):
            result_link = "https://twitter.com/intent/tweet?text=%E7%A7%81%E3%81%AF{}%E5%80%8B%E3%81%AE%E3%82%A2%E3%82%A4%E3%82%B9%E3%82%92Get%E3%81%97%E3%81%9F%E3%82%88!!%0A%23KAITO%E3%81%AE%E3%82%A2%E3%82%A4%E3%82%B9%E3%82%A2%E3%83%84%E3%83%A1%0A%0Ahttps%3A%2F%2Fkitao.github.io%2Fpyxel%2Fwasm%2Flauncher%2F%3Frun%3DKashikosen.Snake_KAITO_18.Snake_KAITO"
            result_score = self.score
            form_score = result_link.format(result_score)
            webbrowser.open(form_score)

        
    
    #画面分岐
    def draw(self):
        if self.current_game_state == GameState.GAME_TITLE:
            self.draw_game_title()
        elif self.current_game_state == GameState.RUNNING:
            self.draw_running()
        elif self.current_game_state == GameState.GAME_OVER:
            self.draw_game_over()
        
        

    




App()