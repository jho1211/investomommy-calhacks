import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";

type MonteCarloData = {
  ticker: string;
  spot_price: number;
  mu_annual: number;
  sigma_annual: number;
  mean_return: number;
  std_return: number;
  var95_return: number;
  es95_return: number;
  mean_pnl: number;
  std_pnl: number;
  var95_pnl: number;
  es95_pnl: number;
  histogram_url: string; // base64 or data URL
  paths_url: string;     // base64 or data URL
  params: {
    years_history: number;
    horizon_years: number;
    steps_per_year: number;
    n_paths: number;
  };
  // optional extras if you ever add them:
  percentiles?: { p5: number; p50: number; p95: number };
  horizonDays?: number;
};

function ensureDataUrl(src: string): string {
  if (!src) return "";
  if (src.startsWith("data:")) return src;
  // Heuristic: if it looks like base64, prefix as PNG; otherwise assume it’s already a URL
  const isBase64 = /^[A-Za-z0-9+/=\s]+$/.test(src) && !src.includes("://");
  return isBase64 ? `data:image/png;base64,${src}` : src;
}

// ---- Normal inverse CDF (Acklam) + helpers to compute percentiles analytically (no simulations)
function erf(x: number) {
  const sign = Math.sign(x);
  const a1 = 0.278393, a2 = 0.230389, a3 = 0.000972, a4 = 0.078108;
  const ax = Math.abs(x);
  const t = 1 / (1 + a1*ax + a2*ax*ax + a3*ax*ax*ax + a4*ax*ax*ax*ax);
  return sign * (1 - Math.pow(t, 4));
}
function normInv(p: number) {
  const pp = Math.min(Math.max(p, Number.EPSILON), 1 - Number.EPSILON);
  const a1=-39.6968302866538,a2=220.9460984245205,a3=-275.9285104469687,a4=138.3577518672690,a5=-30.66479806614716,a6=2.506628277459239;
  const b1=-54.47609879822406,b2=161.5858368580409,b3=-155.6989798598866,b4=66.80131188771972,b5=-13.28068155288572;
  const c1=-0.007784894002430293,c2=-0.3223964580411365,c3=-2.400758277161838,c4=-2.549732539343734,c5=4.374664141464968,c6=2.938163982698783;
  const d1=0.007784695709041462,d2=0.3224671290700398,d3=2.445134137142996,d4=3.754408661907416;
  const plow=0.02425,phigh=1-plow;
  let q,r,x;
  if (pp < plow) {
    q = Math.sqrt(-2*Math.log(pp));
    x = (((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
        ((((d1*q + d2)*q + d3)*q + d4)*q + 1);
  } else if (pp <= phigh) {
    q = pp - 0.5; r = q*q;
    x = (((((a1*r + a2)*r + a3)*r + a4)*r + a5)*r + a6) * q /
        (((((b1*r + b2)*r + b3)*r + b4)*r + b5)*r + 1);
  } else {
    q = Math.sqrt(-2*Math.log(1-pp));
    x = -(((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
          ((((d1*q + d2)*q + d3)*q + d4)*q + 1);
  }
  const e = 0.5*(1+erf(x/Math.SQRT2)) - pp;
  const u = e * Math.sqrt(2*Math.PI) * Math.exp(x*x/2);
  return x - u / (1 + x*u/2);
}
function lognormalQuantile(p: number, S0: number, mu: number, sigma: number, T: number) {
  const m = Math.log(S0) + (mu - 0.5*sigma*sigma)*T;
  const s = sigma * Math.sqrt(T);
  return Math.exp(m + s*normInv(p));
}

function prettyDollar(v: number) {
  return `$${Number.isFinite(v) ? v.toFixed(0) : "-"}`;
}

export function MonteCarloChart({ data }: { data: MonteCarloData }) {
  const [view, setView] = useState<"paths" | "histogram">("paths");

  const pathsSrc = ensureDataUrl(data.paths_url);
  const histSrc = ensureDataUrl(data.histogram_url);

  // Analytic percentiles (only if server didn’t provide them)
  const { p5, p50, p95, horizonDays } = useMemo(() => {
    const T = Number(data.params?.horizon_years ?? 1);
    const S0 = Number(data.spot_price);
    const mu = Number(data.mu_annual);
    const sigma = Number(data.sigma_annual);
    const ok = Number.isFinite(T) && T > 0 && Number.isFinite(S0) && S0 > 0 &&
              Number.isFinite(mu) && Number.isFinite(sigma) && sigma >= 0;
    const fromServer = data.percentiles;
    return {
      p5: fromServer?.p5 ?? (ok ? lognormalQuantile(0.05, S0, mu, sigma, T) : NaN),
      p50: fromServer?.p50 ?? (ok ? lognormalQuantile(0.50, S0, mu, sigma, T) : NaN),
      p95: fromServer?.p95 ?? (ok ? lognormalQuantile(0.95, S0, mu, sigma, T) : NaN),
      horizonDays: data.horizonDays ?? Math.round((Number.isFinite(T) ? T : 1) * 252),
    };
  }, [data]);

  const hasBoth = Boolean(pathsSrc) && Boolean(histSrc);

  return (
    <div className="w-full">
      {/* Top meta bar */}
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-muted-foreground">
          Horizon: {horizonDays} days • {data.params?.n_paths ?? 0} paths
        </div>
        <div className="text-xs text-muted-foreground space-x-3">
          <span>P5: <span className="font-medium">{prettyDollar(p5)}</span></span>
          <span>Median: <span className="font-medium">{prettyDollar(p50)}</span></span>
          <span>P95: <span className="font-medium">{prettyDollar(p95)}</span></span>
        </div>
      </div>

      {/* Image container */}
      <div className="rounded-xl border bg-background p-2">
        {/* toolbar */}
        {hasBoth && (
          <div className="mb-2 flex gap-2">
            <Button
              variant={view === "paths" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("paths")}
            >
              Paths
            </Button>
            <Button
              variant={view === "histogram" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("histogram")}
            >
              Histogram
            </Button>
          </div>
        )}

        <div className="h-56 w-full overflow-hidden rounded-lg bg-secondary/20 flex items-center justify-center">
          {view === "paths" ? (
            pathsSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={pathsSrc}
                alt={`${data.ticker} Monte Carlo paths`}
                className="h-full w-auto object-contain"
              />
            ) : (
              <div className="text-sm text-muted-foreground">No paths image available.</div>
            )
          ) : (
            histSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={histSrc}
                alt={`${data.ticker} Monte Carlo histogram`}
                className="h-full w-auto object-contain"
              />
            ) : (
              <div className="text-sm text-muted-foreground">No histogram image available.</div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
