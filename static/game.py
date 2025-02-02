import asyncio

from js import Math, console, document
from pyodide.ffi import create_proxy


# DOM読み込み待機用関数
async def wait_for_dom():
    while document.readyState != "complete":
        await asyncio.sleep(0.1)

async def main():
    await wait_for_dom()

    canvas = document.getElementById("gameCanvas")
    if not canvas:
        console.log("canvasが見つからない")
        return
    ctx = canvas.getContext("2d")
    WIDTH = canvas.width
    HEIGHT = canvas.height

    # グローバル変数としてゲームの状態を管理
    global game_over, fire_cooldown, spaceship, bullets, aliens, alien_direction, alien_speed, score
    game_over = False
    fire_cooldown = 0

    # ゲームの初期化処理
    def reset_game():
        global game_over, fire_cooldown, spaceship, bullets, aliens, alien_direction, alien_speed, score
        game_over = False
        fire_cooldown = 0

        # プレイヤー設定
        spaceship = {
            "x": WIDTH // 2 - 20,
            "y": HEIGHT - 40,
            "width": 40,
            "height": 20,
            "speed": 5
        }

        # 弾リスト
        bullets = []

        # 敵（インベーダー）の設定
        alien_rows = 4
        alien_cols = 8
        alien_padding = 10
        alien_width = 30
        alien_height = 20
        aliens.clear()  # 再生成時にリストをクリア
        start_x = 50
        start_y = 50

        for row in range(alien_rows):
            for col in range(alien_cols):
                alien = {
                    "x": start_x + col * (alien_width + alien_padding),
                    "y": start_y + row * (alien_height + alien_padding),
                    "width": alien_width,
                    "height": alien_height
                }
                aliens.append(alien)

        # 敵の移動設定
        alien_direction = 1  # 1:右, -1:左
        alien_speed = 1.5  # 初期速度

        # スコア管理
        score = 0

    # 初回のゲーム開始
    aliens = []  # `reset_game()` で初期化するための空リスト
    reset_game()

    # キー管理
    keys = {}

    # イベントハンドラ
    def on_key_down(event):
        global game_over
        if game_over and event.key == " ":
            reset_game()
            return

        keys[event.key] = True

    def on_key_up(event):
        keys[event.key] = False

    global keydown_proxy, keyup_proxy
    keydown_proxy = create_proxy(on_key_down)
    keyup_proxy = create_proxy(on_key_up)
    document.addEventListener("keydown", keydown_proxy)
    document.addEventListener("keyup", keyup_proxy)

    def fire_bullet():
        global fire_cooldown
        if fire_cooldown <= 0:
            bullet = {
                "x": spaceship["x"] + spaceship["width"] // 2 - 2,
                "y": spaceship["y"],
                "width": 4,
                "height": 10,
                "speed": 7
            }
            bullets.append(bullet)
            fire_cooldown = 12  # クールダウン（12フレーム = 0.2秒）

    def get_alien_speed():
        """ 画面上の最も下にいる敵の `y` 座標に応じて速度を変化させる """
        if not aliens:
            return alien_speed  # 敵がいなくなったら基本速度
        lowest_y = max(alien["y"] for alien in aliens)
        return alien_speed + (lowest_y / HEIGHT) * 1.5  # 下に行くほど速く

    def update_game():
        global alien_direction, game_over, fire_cooldown

        if game_over:
            return

        # プレイヤー移動（左右）
        if keys.get("ArrowLeft"):
            spaceship["x"] -= spaceship["speed"]
        if keys.get("ArrowRight"):
            spaceship["x"] += spaceship["speed"]
        spaceship["x"] = max(0, min(spaceship["x"], WIDTH - spaceship["width"]))

        # 連射処理
        if keys.get(" ") and fire_cooldown <= 0:
            fire_bullet()
        if fire_cooldown > 0:
            fire_cooldown -= 1

        # 弾移動
        for bullet in bullets[:]:
            bullet["y"] -= bullet["speed"]
            if bullet["y"] + bullet["height"] < 0:
                bullets.remove(bullet)

        # 敵全体の移動処理
        move_down = False
        alien_speed = get_alien_speed()

        for alien in aliens:
            alien["x"] += alien_speed * alien_direction
            if alien["x"] < 0 or alien["x"] + alien["width"] > WIDTH:
                move_down = True

        if move_down:
            alien_direction *= -1
            for alien in aliens:
                alien["y"] += 10

        # 衝突判定（弾と敵）
        for bullet in bullets[:]:
            for alien in aliens[:]:
                if (bullet["x"] < alien["x"] + alien["width"] and
                    bullet["x"] + bullet["width"] > alien["x"] and
                    bullet["y"] < alien["y"] + alien["height"] and
                    bullet["y"] + bullet["height"] > alien["y"]):
                    try:
                        aliens.remove(alien)
                        bullets.remove(bullet)
                        global score
                        score += 100
                    except ValueError:
                        pass
                    break

        # ゲームオーバー判定
        if not aliens:
            game_over = True

    def draw_game():
        ctx.clearRect(0, 0, WIDTH, HEIGHT)

        if game_over:
            ctx.fillStyle = "white"
            ctx.font = "30px sans-serif"
            ctx.fillText("GAME OVER", WIDTH // 2 - 80, HEIGHT // 2)
            ctx.font = "20px sans-serif"
            ctx.fillText("Press SPACE to Restart", WIDTH // 2 - 100, HEIGHT // 2 + 40)
            return

        # プレイヤー描画
        ctx.fillStyle = "lime"
        ctx.fillRect(spaceship["x"], spaceship["y"], spaceship["width"], spaceship["height"])

        # 弾描画
        ctx.fillStyle = "white"
        for bullet in bullets:
            ctx.fillRect(bullet["x"], bullet["y"], bullet["width"], bullet["height"])

        # 敵描画
        ctx.fillStyle = "red"
        for alien in aliens:
            ctx.fillRect(alien["x"], alien["y"], alien["width"], alien["height"])

        # スコア表示
        ctx.fillStyle = "white"
        ctx.font = "20px sans-serif"
        ctx.fillText("Score: " + str(score), 10, 30)

    while True:
        update_game()
        draw_game()
        await asyncio.sleep(1/60)

asyncio.create_task(main())

asyncio.create_task(main())
