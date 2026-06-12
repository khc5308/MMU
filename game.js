// Fix The MMU - Web Version
// 알고리즘과 구현 방식을 Python 원본과 동일하게 1:1 포팅

(function() {
"use strict";

const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");

// 스프라이트시트 로딩 후 게임 시작
const sheet = new Image();
sheet.src = "spritesheet.png";
sheet.onload = init;

// 오프스크린 캔버스로 스프라이트 추출 및 색상 변환
function extractSprite(sx, sy, sw, sh) {
    const c = document.createElement("canvas");
    c.width = sw; c.height = sh;
    c.getContext("2d").drawImage(sheet, sx, sy, sw, sh, 0, 0, sw, sh);
    return c;
}

function scaleSprite(sprite, w, h) {
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const x = c.getContext("2d");
    x.imageSmoothingEnabled = false;
    x.drawImage(sprite, 0, 0, w, h);
    return c;
}

function changeColor(sprite, r, g, b) {
    const c = document.createElement("canvas");
    const w = sprite.width, h = sprite.height;
    c.width = w; c.height = h;
    const x = c.getContext("2d");
    x.drawImage(sprite, 0, 0);
    const d = x.getImageData(0, 0, w, h);
    const p = d.data;
    // BLEND_RGBA_MULT 동등: 각 채널을 color/255로 곱함
    const rm = r / 255, gm = g / 255, bm = b / 255;
    for (let i = 0; i < p.length; i += 4) {
        p[i]     = (p[i]     * rm) | 0;
        p[i + 1] = (p[i + 1] * gm) | 0;
        p[i + 2] = (p[i + 2] * bm) | 0;
    }
    x.putImageData(d, 0, 0);
    return c;
}

function init() {
    // 스프라이트 추출
    const rawMmu    = extractSprite(0, 0, 40, 20);
    const rawPlayer = extractSprite(40, 10, 15, 16);
    const rawNote   = extractSprite(40, 0, 15, 10);
    const rawFire   = extractSprite(26, 20, 14, 6);

    // 스케일 (PLAYER_SCALE = 4)
    const mmuImg    = scaleSprite(rawMmu, 160, 80);
    const playerImg = scaleSprite(rawPlayer, 60, 64);
    const fireImg   = scaleSprite(rawFire, 56, 24);

    // 고정 좌표 하드코딩 (Python 원본과 동일)
    const mmuConstX  = 920;
    const mmuConstY  = 710;
    const fireConstX = 872;
    const fireConstY = 738;
    const playerHalfW = 30;
    const playerHalfH = 32;

    // 배경 생성 (오프스크린 캔버스에 별 미리 렌더링)
    const bgCanvas = document.createElement("canvas");
    bgCanvas.width = 2000; bgCanvas.height = 1500;
    const bgCtx = bgCanvas.getContext("2d");
    bgCtx.fillStyle = "#000";
    bgCtx.fillRect(0, 0, 2000, 1500);
    bgCtx.fillStyle = "#fff";
    for (let gx = 0; gx < 2000; gx += 100) {
        for (let gy = 0; gy < 1500; gy += 100) {
            for (let s = 0; s < 2; s++) {
                const sx = gx + ((Math.random() * 99) | 0);
                const sy = gy + ((Math.random() * 99) | 0);
                if (sx < 2000 && sy < 1500) bgCtx.fillRect(sx, sy, 2, 2);
            }
        }
    }

    // 노트 색상 및 생성
    const noteColors = [
        [137, 207, 240],
        [255, 255, 255],
        [0, 51, 153],
        [255, 255, 0],
        [255, 0, 0],
        [255, 105, 180]
    ];

    const notes = [];
    const uiSlots = [];
    for (let i = 0; i < 6; i++) {
        const rgb = noteColors[i];
        const img = changeColor(rawNote, rgb[0], rgb[1], rgb[2]);
        const dr = Math.max(35, (rgb[0] * 0.25) | 0);
        const dg = Math.max(35, (rgb[1] * 0.25) | 0);
        const db = Math.max(35, (rgb[2] * 0.25) | 0);
        const dimmedImg = changeColor(rawNote, dr, dg, db);

        const nx = 50 + ((Math.random() * 1900) | 0);
        const ny = 50 + ((Math.random() * 1400) | 0);
        const rx = nx - 7;
        const ry = ny - 5;

        notes[i] = {
            bit: 1 << i,
            x: nx,
            y: ny,
            rx: rx,
            ry: ry,
            img: img,
            dimmedImg: dimmedImg
        };
        uiSlots[i] = dimmedImg;
    }

    // 게임 상태 변수
    let collectedMask = 0;
    let endingState = false;
    let shakeFrames = 0;
    let shakeTriggered = false;
    let playerX = (Math.random() * 2000) | 0;
    let playerY = (Math.random() * 1500) | 0;

    // 키 입력 상태 (keydown/keyup 이벤트 기반)
    const keys = {};
    document.addEventListener("keydown", function(e) { keys[e.code] = 1; });
    document.addEventListener("keyup",   function(e) { keys[e.code] = 0; });

    let lastTime = 0;

    function loop(now) {
        const dt = now - lastTime;
        lastTime = now;

        if (endingState) {
            // 엔딩 화면 렌더링
            ctx.fillStyle = "rgb(10,10,15)";
            ctx.fillRect(0, 0, 800, 600);
            ctx.strokeStyle = "rgb(0,100,255)";
            ctx.lineWidth = 2;
            ctx.strokeRect(20, 20, 760, 560);

            ctx.drawImage(fireImg, 272, 208);
            ctx.drawImage(mmuImg, 320, 180);
            ctx.drawImage(playerImg, 460, 188);

            // 텍스트 펄싱
            const pulse = ((now / 8) | 0) % 200;
            const gv = pulse < 100 ? pulse : 200 - pulse;
            const gr = (137 + gv * 1.18) | 0;
            const gg = (207 + gv * 0.48) | 0;

            ctx.textAlign = "center";
            ctx.font = "bold 40px sans-serif";
            ctx.fillStyle = "rgb(" + gr + "," + gg + ",240)";
            ctx.fillText("MISSION SUCCESS!", 400, 365);

            ctx.font = "20px sans-serif";
            ctx.fillStyle = "rgb(200,200,200)";
            ctx.fillText("The MMU is repaired! Now we can head to MIXXTOPIA.", 400, 415);

            ctx.font = "16px sans-serif";
            ctx.fillStyle = "rgb(120,120,120)";
            ctx.fillText("Press [ESC] to Restart", 400, 475);

            if (keys["Escape"]) location.reload();

            requestAnimationFrame(loop);
            return;
        }

        // speed_dt = dt * 0.3 (SPEED=300, dt는 ms 단위)
        let speedDt = dt * 0.3;

        // 치트키 C
        if (keys["KeyC"] && collectedMask !== 63) {
            for (let i = 0; i < 6; i++) {
                const n = notes[i];
                if (!(collectedMask & n.bit)) {
                    bgCtx.fillStyle = "#000";
                    bgCtx.fillRect(n.rx, n.ry, 15, 10);
                    uiSlots[i] = n.img;
                }
            }
            collectedMask = 63;
        }

        // 흔들림 또는 이동 입력
        let shakeX = 0, shakeY = 0, dx = 0, dy = 0;
        if (shakeFrames > 0) {
            shakeFrames--;
            shakeX = ((Math.random() * 13) | 0) - 6;
            shakeY = ((Math.random() * 13) | 0) - 6;
            if (shakeFrames === 0) endingState = true;
        } else {
            dx = (keys["KeyD"] | 0) - (keys["KeyA"] | 0);
            dy = (keys["KeyS"] | 0) - (keys["KeyW"] | 0);
            if (dx && dy) speedDt *= 0.7071;
        }

        // 플레이어 좌표 업데이트 (움직일 때만)
        if (dx) {
            playerX += dx * speedDt;
            if (playerX < 0) playerX = 0;
            else if (playerX > 2000) playerX = 2000;
        }
        if (dy) {
            playerY += dy * speedDt;
            if (playerY < 0) playerY = 0;
            else if (playerY > 1500) playerY = 1500;
        }

        // 노트 충돌 체크 (Broadphase 적용)
        if (collectedMask !== 63) {
            for (let i = 0; i < 6; i++) {
                const n = notes[i];
                const nb = n.bit;
                if (!(collectedMask & nb)) {
                    const dnx = playerX - n.x;
                    if (dnx > -40 && dnx < 40) {
                        const dny = playerY - n.y;
                        if (dny > -40 && dny < 40 && dnx * dnx + dny * dny < 1600) {
                            collectedMask |= nb;
                            uiSlots[i] = n.img;
                            bgCtx.fillStyle = "#000";
                            bgCtx.fillRect(n.rx, n.ry, 15, 10);
                        }
                    }
                }
            }
        } else if (!shakeTriggered) {
            // MMU 충돌 체크
            const dmx = playerX - 1000;
            if (dmx > -80 && dmx < 80) {
                const dmy = playerY - 750;
                if (dmy > -80 && dmy < 80 && dmx * dmx + dmy * dmy < 6400) {
                    shakeFrames = 90;
                    shakeTriggered = true;
                }
            }
        }

        // 카메라 좌표 (분기문으로 clamp)
        let camX = playerX - 400;
        if (camX < 0) camX = 0;
        else if (camX > 1200) camX = 1200;

        let camY = playerY - 300;
        if (camY < 0) camY = 0;
        else if (camY > 900) camY = 900;

        const cx = (camX | 0), cy = (camY | 0);

        // 배경 렌더링
        ctx.drawImage(bgCanvas, -cx + shakeX, -cy + shakeY);

        // 엔진 화염 렌더링 (모두 모았을 경우)
        if (collectedMask === 63) {
            ctx.drawImage(fireImg, fireConstX - cx + shakeX, fireConstY - cy + shakeY);
        }

        // MMU 렌더링
        ctx.drawImage(mmuImg, mmuConstX - cx + shakeX, mmuConstY - cy + shakeY);

        // 노트 렌더링
        if (collectedMask !== 63) {
            for (let i = 0; i < 6; i++) {
                const n = notes[i];
                if (!(collectedMask & n.bit)) {
                    ctx.drawImage(n.img, n.rx - cx + shakeX, n.ry - cy + shakeY);
                }
            }
        }

        // 플레이어 렌더링
        ctx.drawImage(playerImg, (playerX | 0) - cx - playerHalfW + shakeX, (playerY | 0) - cy - playerHalfH + shakeY);

        // UI 슬롯 렌더링 (루프 없이 직접)
        ctx.drawImage(uiSlots[0], 10, 10);
        ctx.drawImage(uiSlots[1], 30, 10);
        ctx.drawImage(uiSlots[2], 50, 10);
        ctx.drawImage(uiSlots[3], 70, 10);
        ctx.drawImage(uiSlots[4], 90, 10);
        ctx.drawImage(uiSlots[5], 110, 10);

        requestAnimationFrame(loop);
    }

    requestAnimationFrame(function(t) { lastTime = t; requestAnimationFrame(loop); });
}

})();
