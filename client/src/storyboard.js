const API = "/api/v1";

const vars = { trauma: true, walk: true, mba: true };
const film = document.getElementById("film");
const layerDark = document.getElementById("layer-dark");
const divider = document.getElementById("divider");
const handle = document.getElementById("handle");
const elMap = {
  trauma: ["el-mom-b", "el-linda"],
  walk: ["el-dog"],
  mba: ["el-diploma"],
};

function setPos(p) {
  const pos = Math.max(4, Math.min(96, p));
  layerDark.style.clipPath = `inset(0 ${100 - pos}% 0 0)`;
  divider.style.left = `${pos}%`;
  handle.style.left = `${pos}%`;
}

setPos(50);
let dragging = false;
film.addEventListener("pointerdown", (e) => {
  dragging = true;
  film.setPointerCapture(e.pointerId);
  move(e);
});
film.addEventListener("pointermove", (e) => {
  if (dragging) move(e);
});
film.addEventListener("pointerup", () => {
  dragging = false;
});
film.addEventListener("pointercancel", () => {
  dragging = false;
});

function move(e) {
  const r = film.getBoundingClientRect();
  setPos(((e.clientX - r.left) / r.width) * 100);
}

function applyElementVisibility(visibility) {
  Object.entries(elMap).forEach(([key, ids]) => {
    const opacity = visibility
      ? visibility[ids[0]] ?? (vars[key] ? 1 : 0.12)
      : vars[key]
        ? 1
        : 0.12;
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.opacity = String(opacity);
    });
  });
}

function renderMetrics(metrics, winContrib) {
  const root = document.getElementById("metrics");
  root.innerHTML = metrics
    .map((m) => {
      const good = m.inverse
        ? m.current_value < m.base_value * 0.75
        : m.current_value > m.base_value * 1.5;
      const col = good ? "#7AAD79" : "#C9A05A";
      const wBase = Math.round((m.base_value / m.max_value) * 100);
      const wNow = Math.round((m.current_value / m.max_value) * 100);
      return `<div class="mrow">
      <div class="mh"><span class="mn">${m.name}</span><span class="mv" style="color:${col}">${m.base_value}${m.unit} → ${m.current_value}${m.unit}</span></div>
      <div class="bars">
        <div class="bt"><div class="bf" style="width:${wBase}%;background:#5A6678"></div></div>
        <div class="bt"><div class="bf" style="width:${wNow}%;background:${col}"></div></div>
      </div>
    </div>`;
    })
    .join("");

  const cn = document.getElementById("contrib-num");
  cn.textContent = `+${Number(winContrib).toFixed(1)}%`;
  cn.style.color = winContrib >= 6 ? "#7AAD79" : "#C9A05A";
}

function applyCaptions(captions) {
  if (captions?.dark) document.getElementById("cap-d").textContent = captions.dark;
  if (captions?.bright) document.getElementById("cap-b").textContent = captions.bright;
}

async function syncEngine() {
  const res = await fetch(`${API}/storyboard/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variables: vars }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function refreshFromEngine() {
  const data = await syncEngine();
  renderMetrics(data.metrics, data.win_contribution_percent);
  applyCaptions(data.captions);
  applyElementVisibility(data.element_visibility);
}

async function toggleVar(key) {
  vars[key] = !vars[key];
  document.getElementById(`v-${key}`).classList.toggle("on", vars[key]);
  try {
    await refreshFromEngine();
  } catch (err) {
    console.error(err);
  }
}

document.querySelectorAll(".vchip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const key = chip.id.replace("v-", "");
    void toggleVar(key);
  });
});

async function genCaptions() {
  const btn = document.getElementById("ai-btn");
  btn.disabled = true;
  btn.textContent = "🎬 导演正在写分镜旁白...";
  try {
    const res = await fetch(`${API}/storyboard/captions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(vars),
    });
    if (!res.ok) throw new Error(await res.text());
    applyCaptions(await res.json());
  } catch {
    await refreshFromEngine();
  }
  btn.disabled = false;
  btn.textContent = "🎬 AI 重新生成双时间线旁白";
}

document.getElementById("ai-btn").addEventListener("click", () => {
  void genCaptions();
});

void refreshFromEngine().catch((err) => {
  console.error(err);
  document.getElementById("cap-d").textContent =
    "引擎连接失败，请确认后端已启动。";
});
