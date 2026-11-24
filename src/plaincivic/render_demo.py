"""Render self-contained WCAG-AAA Accessible & Bilingual HTML Demo from saved PlainCivic runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "cases"
RUNS_DIR = ROOT / "runs"
DEMO_DIR = ROOT / "demo"


def build_payload(primary_run: str = "skill_v2_low") -> dict[str, Any]:
    cases_by_id: dict[str, Any] = {}
    for p in sorted(CASES_DIR.glob("C*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        cases_by_id[d["case_id"]] = d

    summaries: list[dict[str, Any]] = []
    for sp in sorted(RUNS_DIR.glob("*/summary.json")):
        summaries.append(json.loads(sp.read_text(encoding="utf-8")))

    primary_dir = RUNS_DIR / primary_run
    entries: list[dict[str, Any]] = []
    for cid, case in cases_by_id.items():
        tr_path = primary_dir / cid / "trace.json"
        rd_path = primary_dir / cid / "readiness.json"
        if not tr_path.exists() or not rd_path.exists():
            continue
        trace = json.loads(tr_path.read_text(encoding="utf-8"))
        readiness = json.loads(rd_path.read_text(encoding="utf-8"))
        entries.append(
            {
                "case": case,
                "readiness": readiness,
                "trace": {
                    "mode": trace.get("mode"),
                    "thinking_mode": trace.get("thinking_mode"),
                    "stage_a_parsed": trace.get("stage_a_parsed"),
                    "stage_a_reasoning": (trace.get("stage_a_spark") or {}).get("reasoning_content", ""),
                    "stage_a_wall_s": (trace.get("stage_a_spark") or {}).get("wall_seconds", 0),
                    "stage_a_tps": (trace.get("stage_a_spark") or {}).get("tokens_per_sec", 0),
                    "stage_b_reasoning": (trace.get("stage_b_spark") or {}).get("reasoning_content", ""),
                    "stage_b_raw": (trace.get("stage_b_spark") or {}).get("content", ""),
                    "stage_b_wall_s": (trace.get("stage_b_spark") or {}).get("wall_seconds", 0),
                    "stage_b_tps": (trace.get("stage_b_spark") or {}).get("tokens_per_sec", 0),
                    "plain_language_summary_zh": trace.get("plain_language_summary_zh", ""),
                    "plain_language_steps_zh": trace.get("plain_language_steps_zh", []),
                    "bilingual_summary_en": trace.get("bilingual_summary_en", ""),
                    "bilingual_steps_en": trace.get("bilingual_steps_en", []),
                    "stage_c_repairs": trace.get("stage_c_repairs", []),
                    "pre_repair_strict": trace.get("pre_repair_strict"),
                    "skillhub_strict": trace.get("skillhub_strict"),
                    "quote_check": trace.get("quote_check"),
                    "audit": trace.get("audit"),
                },
            }
        )
    return {
        "primary_run": primary_run,
        "summaries": summaries,
        "entries": entries,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>PlainCivic · 办事明鉴 — Bilingual &amp; Accessible Public-Service Readiness Checker</title>
<style>
  :root {
    --bg: #f6f8fb;
    --surface: #ffffff;
    --surface-2: #eef2f7;
    --text: #101828;
    --muted: #475467;
    --border: #d0d5dd;
    --accent: #1d4ed8;
    --accent-soft: #dbeafe;
    --ok: #15803d;
    --ok-bg: #dcfce7;
    --warn: #b45309;
    --warn-bg: #fef3c7;
    --bad: #b91c1c;
    --bad-bg: #fee2e2;
    --na: #475467;
    --na-bg: #f1f5f9;
    --font-size: 15px;
    --line-height: 1.65;
  }
  body.mode-elderly {
    --bg: #0b0f14;
    --surface: #111827;
    --surface-2: #1f2937;
    --text: #ffffff;
    --muted: #facc15;
    --border: #facc15;
    --accent: #fde047;
    --accent-soft: #3f3600;
    --ok: #4ade80;
    --ok-bg: #052e16;
    --warn: #fde047;
    --warn-bg: #422006;
    --bad: #fca5a5;
    --bad-bg: #450a0a;
    --na: #e5e7eb;
    --na-bg: #1f2937;
    --font-size: 21px;
    --line-height: 1.85;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: var(--font-size);
    line-height: var(--line-height);
  }
  .skip-link {
    position: absolute; left: -999px; top: 0;
    background: var(--accent); color: #fff; padding: 8px 14px; z-index: 99;
  }
  .skip-link:focus { left: 10px; top: 10px; }
  header {
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    padding: 16px 24px;
    position: sticky; top: 0; z-index: 20;
  }
  .header-row {
    max-width: 1360px; margin: 0 auto;
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;
  }
  .brand h1 { margin: 0; font-size: 1.35em; letter-spacing: -0.01em; }
  .brand p { margin: 2px 0 0; font-size: 0.85em; color: var(--muted); }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; }
  button.ctrl {
    border: 2px solid var(--border);
    background: var(--surface-2);
    color: var(--text);
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.9em;
  }
  button.ctrl.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }
  body.mode-elderly button.ctrl.active { color: #000; }
  main { max-width: 1360px; margin: 18px auto 48px; padding: 0 20px; }
  .case-strip {
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px;
  }
  .case-btn {
    border: 2px solid var(--border);
    background: var(--surface);
    color: var(--text);
    padding: 8px 12px;
    border-radius: 10px;
    cursor: pointer;
    text-align: left;
    font-size: 0.86em;
  }
  .case-btn.active { border-color: var(--accent); background: var(--accent-soft); }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 0.78em; font-weight: 700; margin-left: 4px;
  }
  .b-ready { background: var(--ok-bg); color: var(--ok); border: 1px solid var(--ok); }
  .b-not_ready, .b-missing, .b-expired, .b-conflict { background: var(--bad-bg); color: var(--bad); border: 1px solid var(--bad); }
  .b-needs_confirmation { background: var(--warn-bg); color: var(--warn); border: 1px solid var(--warn); }
  .b-not_applicable { background: var(--na-bg); color: var(--na); border: 1px solid var(--na); }

  .banner {
    border-radius: 14px; padding: 18px 22px; margin-bottom: 18px;
    border: 2px solid var(--border);
    background: var(--surface);
  }
  .banner.st-not_ready { border-color: var(--bad); background: var(--bad-bg); }
  .banner.st-ready { border-color: var(--ok); background: var(--ok-bg); }
  .banner.st-needs_confirmation { border-color: var(--warn); background: var(--warn-bg); }

  .grid-2 { display: grid; grid-template-columns: 1.3fr 1fr; gap: 18px; align-items: start; }
  @media (max-width: 960px) { .grid-2 { grid-template-columns: 1fr; } }
  .card {
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 18px;
  }
  .card h2 { margin-top: 0; font-size: 1.15em; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
  .req-item {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    background: var(--surface-2);
  }
  .quote-pill {
    display: inline-block; margin-top: 6px; padding: 3px 9px;
    border-radius: 6px; border: 1px solid var(--accent);
    background: var(--accent-soft); color: var(--text);
    cursor: pointer; font-size: 0.85em;
  }
  .src-line {
    padding: 4px 8px; border-radius: 6px; margin-bottom: 4px;
    font-family: ui-monospace, Consolas, monospace; font-size: 0.9em;
  }
  .src-line.hl {
    background: #fde047; color: #000 !important; font-weight: 700;
    outline: 2px solid #ca8a04;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.88em; }
  th, td { border: 1px solid var(--border); padding: 8px 10px; text-align: left; }
  th { background: var(--surface-2); }
  pre {
    background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px;
    overflow-x: auto; font-size: 0.82em; max-height: 360px; white-space: pre-wrap;
  }
  .pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
  .sr-box {
    background: var(--surface); border: 2px dashed var(--accent); padding: 18px;
    border-radius: 12px; white-space: pre-wrap; font-size: 1.02em;
  }
  .hidden { display: none !important; }
</style>
</head>
<body>
<a class="skip-link" href="#main-content">跳到主要核验结论 / Skip to readiness verdict</a>
<header>
  <div class="header-row">
    <div class="brand">
      <h1>PlainCivic · 办事明鉴 <span class="badge b-ready">SkillHub × Spark-X2.6-4B (Local)</span></h1>
      <p>Track: Accessibility &amp; Languages · Skill: <code>global/生活办事材料核验管家@20260716.135124</code> · On-Device Privacy</p>
    </div>
    <div class="toolbar" role="group" aria-label="视图与无障碍模式切换">
      <button class="ctrl active" id="btn-std" onclick="setView('std')">标准核验台</button>
      <button class="ctrl" id="btn-elderly" onclick="setView('elderly')">长辈大字高对比 (WCAG AAA)</button>
      <button class="ctrl" id="btn-bilingual" onclick="setView('bilingual')">中英双语对照 (Bilingual)</button>
      <button class="ctrl" id="btn-sr" onclick="setView('sr')">读屏线性纯文本</button>
      <button class="ctrl" id="btn-bench" onclick="setView('bench')">10案消融与思考预算评测</button>
    </div>
  </div>
</header>

<main id="main-content">
  <div class="case-strip" id="case-strip" role="tablist" aria-label="10个真实与边界政务案例"></div>

  <div id="view-main"></div>
  <div id="view-sr" class="hidden"></div>
  <div id="view-bench" class="hidden"></div>
</main>

<script>
const DATA = __PAYLOAD_JSON__;
let currentIdx = 0;
let currentView = 'std';
let activeHighlight = null;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function setView(mode) {
  currentView = mode;
  document.body.classList.toggle('mode-elderly', mode === 'elderly');
  for (const id of ['std','elderly','bilingual','sr','bench']) {
    document.getElementById('btn-' + id).classList.toggle('active', id === mode);
  }
  document.getElementById('view-main').classList.toggle('hidden', mode === 'sr' || mode === 'bench');
  document.getElementById('view-sr').classList.toggle('hidden', mode !== 'sr');
  document.getElementById('view-bench').classList.toggle('hidden', mode !== 'bench');
  render();
}

function selectCase(idx) {
  currentIdx = idx;
  activeHighlight = null;
  render();
}

function highlightLine(sid, loc) {
  activeHighlight = sid + ':' + loc;
  render();
  const el = document.getElementById('line-' + sid + '-' + loc);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function renderCaseStrip() {
  const strip = document.getElementById('case-strip');
  strip.innerHTML = DATA.entries.map((e, i) => {
    const st = e.readiness.overall_status;
    const match = e.trace.audit.overall_match ? '✓' : '✗';
    return `<button class="case-btn ${i===currentIdx?'active':''}" onclick="selectCase(${i})">
      <strong>${esc(e.case.case_id)}</strong> ${esc(e.case.service)}
      <span class="badge b-${esc(st)}">${esc(st)} (${match})</span>
    </button>`;
  }).join('');
}

function renderMain() {
  const entry = DATA.entries[currentIdx];
  if (!entry) return;
  const c = entry.case;
  const r = entry.readiness;
  const t = entry.trace;
  const stMap = {
    ready: '已就绪 · READY TO GO（材料齐全，可前往办理）',
    not_ready: '未就绪 · DO NOT GO YET（存在阻断项，先补齐再出门）',
    needs_confirmation: '待确认 · NEEDS CONFIRMATION（存在未明身份条件或不可读段落）'
  };
  const strictOk = t.skillhub_strict && t.skillhub_strict.valid;
  const clausesHtml = Object.entries(t.audit.survival_detail || {}).map(([cat, rows]) => {
    return `<div style="margin-bottom:6px"><strong>${esc(cat)}：</strong>` +
      rows.map(x => `<span class="badge ${x.survived?'b-ready':'b-conflict'}">${x.survived?'✓':'✗'} ${esc(x.clause)}</span>`).join('') +
      `</div>`;
  }).join('');

  const reqHtml = (r.requirements || []).map(req => {
    const evBtns = (req.evidence || []).map(ev =>
      `<button class="quote-pill" onclick="highlightLine('${esc(ev.source_id)}','${esc(ev.locator)}')">
        📌 ${esc(ev.source_id)}:${esc(ev.locator)}「${esc(ev.quote)}」
      </button>`
    ).join(' ');
    return `<div class="req-item">
      <div><strong>${esc(req.id)} · ${esc(req.item)}</strong>
        <span class="badge b-${esc(req.status)}">${esc(req.status)}</span>
        <span class="badge b-not_applicable">${esc(req.necessity)} / ${esc(req.applicability)}</span>
      </div>
      ${req.condition ? `<div style="font-size:0.9em;color:var(--muted)">触发条件：${esc(req.condition)}</div>` : ''}
      <div style="margin-top:4px">${esc(req.reason)}</div>
      ${req.matched_inventory_ids && req.matched_inventory_ids.length ? `<div style="font-size:0.86em;color:var(--muted)">匹配现有材料：${esc(req.matched_inventory_ids.join(', '))}</div>` : ''}
      <div>${evBtns}</div>
    </div>`;
  }).join('');

  const stepsZh = (t.plain_language_steps_zh || []).map((s, i) => `<li>${esc(s)}</li>`).join('');
  const stepsEn = (t.bilingual_steps_en || []).map((s, i) => `<li>${esc(s)}</li>`).join('');
  const showEn = currentView === 'bilingual' || (t.bilingual_steps_en && t.bilingual_steps_en.length > 0);

  const srcHtml = (c.sources || []).map(s => {
    const lns = (s.lines || []).map(ln => {
      const m = ln.match(/^(L\d+):/);
      const loc = m ? m[1] : 'L1';
      const key = s.id + ':' + loc;
      return `<div class="src-line ${activeHighlight===key?'hl':''}" id="line-${esc(s.id)}-${esc(loc)}">${esc(ln)}</div>`;
    }).join('');
    return `<div style="margin-bottom:12px">
      <div style="font-weight:700;margin-bottom:4px">[${esc(s.id)}] ${esc(s.filename)} (${esc(s.source_date)} · ${esc(s.currentness)})</div>
      ${lns}
    </div>`;
  }).join('');

  const invHtml = (c.inventory || []).map(it =>
    `<li><strong>${esc(it.id)}</strong>：${esc(it.name)} — ${esc(it.details)}</li>`
  ).join('');

  document.getElementById('view-main').innerHTML = `
    <div class="banner st-${esc(r.overall_status)}">
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:center">
        <strong>${esc(c.case_id)} · ${esc(c.title_zh)}</strong>
        <div>
          <span class="badge ${strictOk?'b-ready':'b-conflict'}">SkillHub validate_readiness.py --strict: ${strictOk?'PASS (0 err / 0 warn)':'FAIL'}</span>
          <span class="badge b-not_applicable">Spark-X2.6-4B (${esc(t.thinking_mode)}) · ${(t.stage_a_wall_s + t.stage_b_wall_s).toFixed(1)}s</span>
        </div>
      </div>
      <h2 style="margin:8px 0 4px;border:none;padding:0">${esc(stMap[r.overall_status] || r.overall_status)}</h2>
      <div><strong>大白话提醒：</strong>${esc(t.plain_language_summary_zh || '见下方逐项核验清单')}</div>
      ${t.bilingual_summary_en ? `<div style="margin-top:4px"><strong>Plain English Verdict:</strong> ${esc(t.bilingual_summary_en)}</div>` : ''}
    </div>

    <div class="grid-2">
      <div>
        <div class="card">
          <h2>1. 无障碍易读办事步骤 ${showEn ? '&amp; Bilingual EN Guide' : ''}</h2>
          <ol>${stepsZh}</ol>
          ${stepsEn ? `<hr/><h3>Plain-English Bilingual Steps</h3><ol>${stepsEn}</ol>` : ''}
          <div style="margin-top:12px">
            <strong>关键条款存活审计（Clause Survival：${t.audit.clause_survived}/${t.audit.clause_total} = ${(t.audit.clause_survival_rate*100).toFixed(1)}%）：</strong>
            ${clausesHtml}
          </div>
        </div>

        <div class="card">
          <h2>2. 逐条材料与条件核验（点击原文引用定位右侧高亮）</h2>
          ${reqHtml}
          ${(r.questions && r.questions.length) ? `<h3>待人工澄清问题</h3><ol>${r.questions.map(q=>`<li>${esc(q)}</li>`).join('')}</ol>` : ''}
        </div>

        <div class="card" id="card-trace">
          <h2>3. 完整执行证据链（Spark-X2.6-4B 原始输出 → Stage C 修复门禁）</h2>
          <p><strong>原文逐字引用命中率：</strong>${t.quote_check.verbatim_hits}/${t.quote_check.total_quotes} (${(t.quote_check.verbatim_rate*100).toFixed(1)}%) ｜ <strong>Stage C 自动护栏修复：</strong>${(t.stage_c_repairs||[]).length} 条</p>
          ${(t.stage_c_repairs && t.stage_c_repairs.length) ? `<ul>${t.stage_c_repairs.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>` : '<p>零契约违规，无需修复。</p>'}
          <details><summary>展开 Stage A（盲提）本地 Spark-X2.6-4B 思考过程与结构化输出 (${t.stage_a_wall_s}s, ${t.stage_a_tps} tok/s)</summary>
            <pre>${esc(t.stage_a_reasoning ? '<think>\n' + t.stage_a_reasoning + '\n</think>\n\n' : '')}${esc(JSON.stringify(t.stage_a_parsed, null, 2))}</pre>
          </details>
          <details style="margin-top:8px"><summary>展开 Stage B（条件与双语核验）本地 Spark-X2.6-4B 思考过程与原始 JSON (${t.stage_b_wall_s}s, ${t.stage_b_tps} tok/s)</summary>
            <pre>${esc(t.stage_b_reasoning ? '<think>\n' + t.stage_b_reasoning + '\n</think>\n\n' : '')}${esc(t.stage_b_raw)}</pre>
          </details>
        </div>
      </div>

      <div>
        <div class="card">
          <h2>原文来源面板（点击左侧证据即定位）</h2>
          <p style="font-size:0.9em;color:var(--muted)">参考日期：<code>${esc(c.reference_date)}</code> ｜ 用户画像：${esc(c.profile_summary)}</p>
          ${srcHtml}
        </div>
        <div class="card">
          <h2>用户现有材料清单（100% 本地推理不上传）</h2>
          <ul>${invHtml}</ul>
        </div>
        <div class="card">
          <h2>来源边界与人工复核提示</h2>
          <ul>${(r.limitations || []).map(l=>`<li>${esc(l)}</li>`).join('')}</ul>
        </div>
      </div>
    </div>
  `;
}

function renderSR() {
  const entry = DATA.entries[currentIdx];
  if (!entry) return;
  const c = entry.case;
  const r = entry.readiness;
  const t = entry.trace;
  const lines = [
    `【读屏友好线性文本报告 · Screen-Reader Linearized Report】`,
    `事项：${c.service}（参考日期：${c.reference_date}）`,
    `整体结论：${r.overall_status} — ${t.plain_language_summary_zh}`,
    t.bilingual_summary_en ? `English Verdict: ${t.bilingual_summary_en}` : '',
    ``,
    `一、分步办事指南：`,
    ...(t.plain_language_steps_zh || []).map((s, i) => `  第${i+1}步：${s.replace(/^第\d+步[：:]\s*/, '')}`),
    ...(t.bilingual_steps_en && t.bilingual_steps_en.length ? [``, `English Steps:`, ...t.bilingual_steps_en.map((s,i)=>`  Step ${i+1}: ${s.replace(/^Step\s*\d+[:：]\s*/i, '')}`)] : []),
    ``,
    `二、逐项材料核对结果：`,
    ...(r.requirements || []).map(req => `  - ${req.id} ${req.item}：状态=${req.status}；原因=${req.reason}；依据=${(req.evidence||[]).map(e=>e.source_id+':'+e.locator+'「'+e.quote+'」').join(' / ')}`),
    ``,
    `三、限制与免责声明：`,
    ...(r.limitations || []).map(l => `  - ${l}`)
  ].filter(Boolean);
  document.getElementById('view-sr').innerHTML = `<div class="sr-box" role="region" aria-label="读屏线性纯文本">${esc(lines.join('\n'))}</div>`;
}

function renderBench() {
  const rank = { baseline_v1_low: 0, skill_v2_none: 1, skill_v2_low: 2, skill_v2_high: 3 };
  const ordered = [...(DATA.summaries || [])].sort((a, b) => (rank[a.run_name] ?? 9) - (rank[b.run_name] ?? 9));
  const rows = ordered.map(s => `<tr>
    <td><strong>${esc(s.run_name)}</strong></td>
    <td>${esc(s.overall_match_count)} (${(s.overall_accuracy*100).toFixed(0)}%)</td>
    <td>${esc(s.trap_pass_count)} (${(s.trap_pass_rate*100).toFixed(0)}%)</td>
    <td>${esc(s.clause_survival_count)} (${(s.clause_survival_rate*100).toFixed(1)}%)</td>
    <td>${esc(s.pre_repair_strict_pass)} → <strong>${esc(s.post_repair_strict_pass)}</strong></td>
    <td>${(s.pre_repair_verbatim_rate*100).toFixed(1)}% → <strong>${(s.post_repair_verbatim_rate*100).toFixed(1)}%</strong></td>
    <td>${esc(s.avg_wall_seconds)}s</td>
    <td>${esc(s.avg_completion_tokens)} tok (${esc(s.avg_tokens_per_sec)} tok/s)</td>
  </tr>`).join('');
  document.getElementById('view-bench').innerHTML = `
    <div class="card">
      <h2>10案全量评测：Baseline v1 vs SkillHub PlainCivic v2 × Spark-X2.6-4B 三档思考预算 (none / low / high)</h2>
      <p>所有 10 个案例与金标准（<code>gold/gold.json</code>、<code>gold/ACCEPTANCE.md</code>）均在首次本地推理前预先 Git 提交锁定（commit <code>61d9137</code>）。</p>
      <table>
        <thead>
          <tr>
            <th>配置 (Run)</th>
            <th>整体决策准确率</th>
            <th>陷阱全过率</th>
            <th>关键条款存活率</th>
            <th>SkillHub --strict 通过 (修复前→后)</th>
            <th>原文逐字引用率 (修复前→后)</th>
            <th>单案平均耗时</th>
            <th>平均输出 Token &amp; 速度</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function render() {
  renderCaseStrip();
  renderMain();
  renderSR();
  renderBench();
}

// Support URL query params for deterministic headless screenshots: ?case=C01&view=bilingual&hl=S1:L6&openTrace=1
(function initFromQuery() {
  const qs = new URLSearchParams(window.location.search);
  const cParam = qs.get('case');
  if (cParam) {
    const idx = DATA.entries.findIndex(e => e.case.case_id === cParam);
    if (idx >= 0) currentIdx = idx;
  }
  const hl = qs.get('hl');
  if (hl) activeHighlight = hl;
  const view = qs.get('view') || 'std';
  setView(view);
  if (qs.get('openTrace') === '1') {
    document.querySelectorAll('#view-main details').forEach(d => d.setAttribute('open', 'open'));
    const tc = document.getElementById('card-trace');
    if (tc && tc.parentElement) {
      tc.parentElement.prepend(tc);
    }
  }
})();
</script>
</body>
</html>
"""


def render_demo(primary_run: str = "skill_v2_low") -> Path:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload(primary_run=primary_run)
    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", json.dumps(payload, ensure_ascii=False))
    out_path = DEMO_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Rendered interactive WCAG-AAA bilingual demo -> {out_path} ({len(payload['entries'])} cases, {len(payload['summaries'])} runs)")
    return out_path


if __name__ == "__main__":
    run_arg = sys.argv[1] if len(sys.argv) > 1 else "skill_v2_low"
    render_demo(run_arg)
