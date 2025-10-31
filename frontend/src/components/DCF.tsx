import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import SensitivityHeatMap from "./SensitivityHeatMap"; 

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

type DcfResponse = {
  dcf_result?: {
    intrinsic_value_per_share?: number | null;
    assumptions?: { wacc?: number | null; terminal_growth?: number | null };
  };
  financials_snapshot?: { totals?: { price?: number | null } };
  sensitivity_grid?: number[][];
};

function usd(n?: number | null) {
  return n == null || isNaN(n) ? "—" : `$${n.toFixed(2)}`;
}
function pct(n?: number | null) {
  return n == null || isNaN(n) ? "—" : `${(n * 100).toFixed(2)}%`;
}

async function fetchDcf(ticker: string): Promise<DcfResponse> {
  const res = await fetch(`${API_BASE_URL}/dcf/${encodeURIComponent(ticker)}?years=10&midyear=true`);
  if (!res.ok) throw new Error(`DCF fetch failed: ${res.status}`);
  return res.json();
}

export default function DCF({ ticker }: { ticker: string }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dcf", ticker],
    queryFn: () => fetchDcf(ticker),
    staleTime: 60 * 1000,
  });

  const { price, ivDyn, wacc, tg, upsideDyn, grid, rowLabels, colLabels } = useMemo(() => {
    const price = data?.financials_snapshot?.totals?.price ?? null;
    const ivDyn = data?.dcf_result?.intrinsic_value_per_share ?? null;
    const wacc = data?.dcf_result?.assumptions?.wacc ?? null;
    const tg = data?.dcf_result?.assumptions?.terminal_growth ?? null;
    const grid = data?.sensitivity_grid ?? null;
    const upsideDyn = price != null && ivDyn != null ? (ivDyn - price) / price : null;

    const toPct = (x: number) => `${(x * 100).toFixed(2)}%`;
    const colLabels = wacc == null ? [] : [-0.0075, 0, 0.0075].map((s) => toPct(wacc + s));
    const rowLabels = tg == null ? [] : [-0.005, 0, 0.005].map((s) => toPct(tg + s));
    return { price, ivDyn, wacc, tg, upsideDyn, grid, rowLabels, colLabels };
  }, [data]);

  if (isLoading)
    return (
      <Card>
        <CardHeader>
          <CardTitle>DCF — Intrinsic Value</CardTitle>
          <CardDescription>Loading valuation…</CardDescription>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">Fetching DCF numbers for {ticker}…</CardContent>
      </Card>
    );

  if (isError)
    return (
      <Card>
        <CardHeader>
          <CardTitle>DCF — Intrinsic Value</CardTitle>
          <CardDescription className="text-destructive">
            {(error as Error)?.message ?? "Failed to load"}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Check that the DCF server is running and CORS is allowed for your frontend origin.
        </CardContent>
      </Card>
    );

  const upClass = (u?: number | null) =>
    u == null
      ? "bg-muted text-foreground"
      : u >= 0
      ? "bg-emerald-600/15 text-emerald-600"
      : "bg-red-600/15 text-red-600";

  return (
    <Card>
      <CardHeader>
        <CardTitle>DCF — Intrinsic Value</CardTitle>
        <CardDescription className="text-muted-foreground">
          {ticker.toUpperCase()} • WACC {pct(wacc)} • Terminal Growth Rate {pct(tg)}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Market price</span>
          <span className="font-medium">{usd(price)}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Intrinsic value (Dynamic)</span>
            <Badge className={upClass(upsideDyn)}>
              {upsideDyn == null ? "—" : `${(upsideDyn * 100).toFixed(1)}%`}
            </Badge>
          </div>
          <span className="font-semibold">{usd(ivDyn)}</span>
        </div>

        <p className="text-xs text-muted-foreground pt-2">
          Intrinsic values are derived from FCFF with a terminal growth model. Numbers are estimates and not investment advice.
        </p>

        {Array.isArray(grid) && grid.length > 0 && (
          <div className="pt-3 border-t">
            <div className="mb-2 font-medium">DCF Sensitivity Heat Map (WACC x Terminal Growth)</div>
            <SensitivityHeatMap grid={grid} rowLabels={rowLabels} colLabels={colLabels} />
            <br/>
            <div className="mt-2 text-xs text-muted-foreground">
              Rows: Terminal Growth (low→high) • Columns: WACC (low→high)
            </div>
            <div className="mb-2 font-medium">Sensitivity Heat Map Explanation</div>
            <p>
                The DCF sensitivity heat graph shows how a company’s value changes when you adjust two things: 
                WACC on the Y-axis and terminal growth on the X-axis. Each square shows the intrinsic value per share 
                based on those assumptions. Lighter colors mean higher values, and darker colors mean lower ones. As WACC 
                goes up, value drops because future cash flows are discounted more. As terminal growth goes up, value rises 
                because you expect the company to grow more in the long run. This graph helps you see how sensitive your 
                valuation is to small changes in your inputs.

            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

