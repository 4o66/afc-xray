// Sweep retract_length per material preset: the largest value that keeps softened material (at or above Tg) below the
// heat break top (Z 35.1). Uses the page's own model and AFC defaults for everything else.
function peakFor(ret, push){ P.ret = ret; P.push = push; layout(); simReset(); seek(T_END); return [SIM.peakSoft, SIM.peakLiq]; }
function maxRet(push0){ var best = null; for (var r = 0; r <= 25.001; r += 0.5){ var pk = peakFor(r, push0); if (pk[0] <= 35.1) best = r; } return best; }
var out = ["tau | material | print C | Tg C | liquid C | max retract_length | softened peak at 20 (AFC default)"];
[2, 3, 5].forEach(function(tau){ ["PLA", "PETG", "ABS", "ASA", "PC"].forEach(function(k){
  P = Object.assign({}, FACTORY, {tau: tau, mat: k}); setMat(k); var m = MATS[k];
  var r = maxRet(15), b = peakFor(20, 15);
  out.push([tau, k, m.tp, m.tg, m.tl, r, b[0].toFixed(1) + " (" + (b[0] - 35.1 >= 0 ? "+" : "") + (b[0] - 35.1).toFixed(1) + ")"].join(" | ")); }); });
var __out = out.join("\n"); if (typeof console !== "undefined" && console.log) console.log(__out); __out;
