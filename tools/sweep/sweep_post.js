// Sweep retract_length per material: the largest value that keeps softened material (at or above Tg) below the heat break top (Z 35.1).
function peakFor(ret, push){ P.ret = ret; P.push = push; layout(); simReset(); seek(T_END); return [SIM.peakSoft, SIM.peakLiq]; }
function maxRet(push0){ var best = null; for (var r = 0; r <= 25.001; r += 0.5){ var pk = peakFor(r, push0); if (pk[0] <= 35.1) best = r; } return best; }
var mats = [["PLA", 210, 60], ["PETG", 240, 80], ["ASA", 265, 100], ["ASA", 255, 100]];
var out = ["tau | material | print C | Tg C | max retract_length | softened peak at 18 | at 20 | at 0"];
[2, 3, 5].forEach(function(tau){ P.tau = tau; mats.forEach(function(m){ TP = m[1]; TG = m[2];
  var r = maxRet(15), a = peakFor(18, 15), b = peakFor(20, 15), c = peakFor(0, 15);
  out.push([tau, m[0], m[1], m[2], r, a[0].toFixed(1), b[0].toFixed(1), c[0].toFixed(1)].join(" | ")); }); });
var __out = out.join("\n"); if (typeof console !== "undefined" && console.log) console.log(__out); __out;
